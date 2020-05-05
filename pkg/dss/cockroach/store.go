package cockroach

import (
	"context"
	"database/sql"
	"errors"
	"fmt"

	"github.com/dpjacques/clockwork"
	"go.uber.org/zap"
)

var (
	// DefaultClock is what is used as the Store's clock, returned from Dial.
	DefaultClock = clockwork.NewRealClock()
)

// Store is an implementation of dss.Store using
// Cockroach DB as its backend store.
type Store struct {
	*sql.DB
	logger *zap.Logger
	clock  clockwork.Clock
}

// Dial returns a Store instance connected to a cockroach instance available at
// "uri".
// https://www.cockroachlabs.com/docs/stable/connection-parameters.html
func Dial(uri string, logger *zap.Logger) (*Store, error) {
	db, err := sql.Open("postgres", uri)
	if err != nil {
		return nil, err
	}

	return &Store{
		DB:     db,
		logger: logger,
		clock:  DefaultClock,
	}, nil
}

// BuildURI returns a cockroachdb connection string from a params map.
func BuildURI(params map[string]string) (string, error) {
	an := params["application_name"]
	if an == "" {
		an = "dss"
	}
	h := params["host"]
	if h == "" {
		return "", errors.New("missing crdb hostname")
	}
	p := params["port"]
	if p == "" {
		return "", errors.New("missing crdb port")
	}
	u := params["user"]
	if u == "" {
		return "", errors.New("missing crdb user")
	}
	ssl := params["ssl_mode"]
	if ssl == "" {
		return "", errors.New("missing crdb ssl_mode")
	}
	if ssl == "disable" {
		return fmt.Sprintf("postgresql://%s@%s:%s?application_name=%s&sslmode=disable", u, h, p, an), nil
	}
	dir := params["ssl_dir"]
	if dir == "" {
		return "", errors.New("missing crdb ssl_dir")
	}

	return fmt.Sprintf(
		"postgresql://%s@%s:%s?application_name=%s&sslmode=%s&sslrootcert=%s/ca.crt&sslcert=%s/client.%s.crt&sslkey=%s/client.%s.key",
		u, h, p, an, ssl, dir, dir, u, dir, u,
	), nil
}

type queryable interface {
	QueryContext(ctx context.Context, query string, args ...interface{}) (*sql.Rows, error)
	QueryRowContext(ctx context.Context, query string, args ...interface{}) *sql.Row
	ExecContext(ctx context.Context, query string, args ...interface{}) (sql.Result, error)
}

// Close closes the underlying DB connection.
func (s *Store) Close() error {
	return s.DB.Close()
}

// Bootstrap bootstraps the underlying database with required tables.
//
// TODO: We should handle database migrations properly, but bootstrap both us
// *and* the database with this manual approach here.
func (s *Store) Bootstrap(ctx context.Context) error {
	/*
			The following tables correspond to the ASTM Remote ID standard A2.5.2.3:
			a) Cell ID:
					cells_identification_service_areas.cell_id
			 		cells_subscriptions.cell_id
			b) Subscription
				 	i. subscriptions.id
				 ii. subscriptions.owner
				iii. subscriptions.url
				 iv. subscriptions.starts_at and subscriptions.ends_at
				  v. the mapping from cells_subscriptions.subscription_id and cell_id
						 to subscriptions.id
				 vi. subscriptions.notification_index
			c) ISA
		 		 	i. identification_service_areas.id
				 ii. identification_service_areas.owner
				iii. identification_service_areas.url
				 iv. identification_service_areas.starts_at and
						 identification_service_areas.ends_at
				  v. the mapping from
						 cells_identification_service_areas.subscription_id and cell_id
						 to cells_identification_service_areas.id
	*/
	const query = `
	CREATE TABLE IF NOT EXISTS subscriptions (
		id UUID PRIMARY KEY,
		owner STRING NOT NULL,
		url STRING NOT NULL,
		notification_index INT4 DEFAULT 0,
		starts_at TIMESTAMPTZ,
		ends_at TIMESTAMPTZ,
		updated_at TIMESTAMPTZ NOT NULL,
		INDEX owner_idx (owner),
		INDEX starts_at_idx (starts_at),
		INDEX ends_at_idx (ends_at),
		CHECK (starts_at IS NULL OR ends_at IS NULL OR starts_at < ends_at)
	);
	CREATE TABLE IF NOT EXISTS cells_subscriptions (
		cell_id INT64 NOT NULL,
		cell_level INT CHECK (cell_level BETWEEN 0 and 30),
		subscription_id UUID NOT NULL REFERENCES subscriptions (id) ON DELETE CASCADE,
		PRIMARY KEY (cell_id, subscription_id),
		INDEX cell_id_idx (cell_id),
		INDEX subscription_id_idx (subscription_id)
	);
	CREATE TABLE IF NOT EXISTS identification_service_areas (
		id UUID PRIMARY KEY,
		owner STRING NOT NULL,
		url STRING NOT NULL,
		starts_at TIMESTAMPTZ,
		ends_at TIMESTAMPTZ,
		updated_at TIMESTAMPTZ NOT NULL,
		INDEX owner_idx (owner),
		INDEX starts_at_idx (starts_at),
		INDEX ends_at_idx (ends_at),
		INDEX updated_at_idx (updated_at),
		CHECK (starts_at IS NULL OR ends_at IS NULL OR starts_at < ends_at)
	);
	CREATE TABLE IF NOT EXISTS cells_identification_service_areas (
		cell_id INT64 NOT NULL,
		cell_level INT CHECK (cell_level BETWEEN 0 and 30),
		identification_service_area_id UUID NOT NULL REFERENCES identification_service_areas (id) ON DELETE CASCADE,
		PRIMARY KEY (cell_id, identification_service_area_id),
		INDEX cell_id_idx (cell_id),
		INDEX identification_service_area_id_idx (identification_service_area_id)
	);
	`
	_, err := s.ExecContext(ctx, query)
	return err
}
