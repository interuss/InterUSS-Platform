package datastore

import (
	"context"
	"fmt"
	"github.com/coreos/go-semver/semver"
	"github.com/interuss/stacktrace"
	"github.com/jackc/pgx/v5/pgxpool"
	"time"
)

type Datastore struct {
	Database
	Version *Version
	Pool    *pgxpool.Pool
}

type Database interface {
	GetSchemaVersion(ctx context.Context, dbName string) (*semver.Version, error)
	DatabaseExists(ctx context.Context, name string) (bool, error)
	CreateDatabase(ctx context.Context, name string) error
}

var UnknownVersion = &semver.Version{}

func Dial(ctx context.Context, connParams ConnectParameters) (*Datastore, error) {
	dsn, err := connParams.BuildDSN()
	if err != nil {
		return nil, stacktrace.Propagate(err, "Failed to create connection config for pgx")
	}

	config, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		return nil, stacktrace.Propagate(err, "Failed to parse connection config for pgx")
	}

	if connParams.SSL.Mode == "enable" {
		config.ConnConfig.TLSConfig.ServerName = connParams.Host
	}
	config.MaxConns = int32(connParams.MaxOpenConns)
	config.MaxConnIdleTime = (time.Duration(connParams.MaxConnIdleSeconds) * time.Second)
	config.HealthCheckPeriod = (1 * time.Second)
	config.MinConns = 1

	dbPool, err := pgxpool.NewWithConfig(ctx, config)
	if err != nil {
		return nil, err
	}

	ds, err := initDatastore(ctx, dbPool)
	if err != nil {
		return nil, stacktrace.Propagate(err, "Failed to connect to datastore")
	}
	return ds, nil
}

func initDatastore(ctx context.Context, pool *pgxpool.Pool) (*Datastore, error) {
	version, err := fetchVersion(ctx, pool)
	if err != nil {
		return nil, err
	}

	if version.IsCockroachDB() {
		return &Datastore{Version: version, Pool: pool}, nil
	}
	return nil, fmt.Errorf("%s is not implemented yet", version.dsName)
}

func fetchVersion(ctx context.Context, pool *pgxpool.Pool) (*Version, error) {
	const versionDbQuery = `
      SELECT version();
    `
	var fullVersion string
	err := pool.QueryRow(ctx, versionDbQuery).Scan(&fullVersion)
	if err != nil {
		return nil, stacktrace.Propagate(err, "Error querying datastore version")
	}

	return VersionFromString(fullVersion)
}

func (ds *Datastore) CreateDatabase(ctx context.Context, dbName string) error {
	createDB := fmt.Sprintf("CREATE DATABASE %s", dbName)
	if _, err := ds.Pool.Exec(ctx, createDB); err != nil {
		return fmt.Errorf("failed to create new database %s: %v", dbName, err)
	}
	return nil
}

func (ds *Datastore) DatabaseExists(ctx context.Context, dbName string) (bool, error) {
	const checkDbQuery = `
		SELECT EXISTS (
			SELECT * FROM pg_database WHERE datname = $1
		)`

	var exists bool
	if err := ds.Pool.QueryRow(ctx, checkDbQuery, dbName).Scan(&exists); err != nil {
		return false, err
	}

	return exists, nil
}

// GetSchemaVersion returns the Schema Version of the requested DB Name
func (ds *Datastore) GetSchemaVersion(ctx context.Context, dbName string) (*semver.Version, error) {
	if dbName == "" {
		return nil, stacktrace.NewError("GetSchemaVersion was provided with an empty database name")
	}

	var (
		checkTableQuery = fmt.Sprintf(`
      SELECT EXISTS (
        SELECT
          *
        FROM
          %s.information_schema.tables
        WHERE
          table_name = 'schema_versions'
        AND
          table_catalog = $1
      )`, dbName)
		exists          bool
		getVersionQuery = `
      SELECT
        schema_version
      FROM
        schema_versions
      WHERE
        onerow_enforcer = TRUE`
	)

	if err := ds.Pool.QueryRow(ctx, checkTableQuery, dbName).Scan(&exists); err != nil {
		return nil, stacktrace.Propagate(err, "Error scanning table listing row")
	}

	if !exists {
		// Database has not been bootstrapped using DB Schema Manager
		return UnknownVersion, nil
	}

	var dbVersion string
	if err := ds.Pool.QueryRow(ctx, getVersionQuery).Scan(&dbVersion); err != nil {
		return nil, stacktrace.Propagate(err, "Error scanning version row")
	}
	if len(dbVersion) > 0 && dbVersion[0] == 'v' {
		dbVersion = dbVersion[1:]
	}

	return semver.NewVersion(dbVersion)
}
