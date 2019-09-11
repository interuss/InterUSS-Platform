package cockroach

import (
	"context"
	"database/sql"
	"errors"
	"flag"
	"testing"
	"time"

	"github.com/google/uuid"
	"github.com/steeling/InterUSS-Platform/pkg/dss"
	"github.com/steeling/InterUSS-Platform/pkg/dss/models"

	"github.com/jonboulle/clockwork"
	"github.com/stretchr/testify/require"
	"go.uber.org/zap"
)

var (
	// Make sure that Store implements dss.Store.
	_ dss.Store = &Store{}

	storeURI  = flag.String("store-uri", "", "URI pointing to a Cockroach node")
	fakeClock = clockwork.NewFakeClock()
	startTime = fakeClock.Now().Add(-time.Minute)
	endTime   = fakeClock.Now().Add(time.Hour)
)

func init() {
	flag.Parse()
}

func setUpStore(ctx context.Context, t *testing.T) (*Store, func() error) {
	// Reset the clock for every test.
	fakeClock = clockwork.NewFakeClock()

	store, err := newStore()
	if err != nil {
		t.Skip(err)
	}
	require.NoError(t, store.Bootstrap(ctx))
	return store, func() error {
		return store.cleanUp(ctx)
	}
}

func newStore() (*Store, error) {
	if len(*storeURI) == 0 {
		return nil, errors.New("Missing command-line parameter store-uri")
	}

	db, err := sql.Open("postgres", *storeURI)
	if err != nil {
		return nil, err
	}

	return &Store{
		DB:     db,
		logger: zap.L(),
		clock:  fakeClock,
	}, nil
}

func TestStoreBootstrap(t *testing.T) {
	var (
		ctx                  = context.Background()
		store, tearDownStore = setUpStore(ctx, t)
	)
	require.NotNil(t, store)
	require.NoError(t, tearDownStore())
}

func TestDatabaseEnsuresBeginsBeforeExpires(t *testing.T) {
	var (
		ctx                  = context.Background()
		store, tearDownStore = setUpStore(ctx, t)
	)
	require.NotNil(t, store)
	defer func() {
		require.NoError(t, tearDownStore())
	}()

	var (
		begins  = time.Now()
		expires = begins.Add(-5 * time.Minute)
	)
	_, err := store.InsertSubscription(ctx, models.Subscription{
		ID:                models.ID(uuid.New().String()),
		Owner:             "me-myself-and-i",
		Url:               "https://no/place/like/home",
		NotificationIndex: 42,
		StartTime:         &begins,
		EndTime:           &expires,
	})
	require.Error(t, err)
}

func TestBuildURI(t *testing.T) {
	cases := []struct {
		name   string
		params map[string]string
		want   string
	}{
		{
			name: "valid URI",
			params: map[string]string{
				"host":             "localhost",
				"port":             "26257",
				"user":             "root",
				"ssl_mode":         "enable",
				"ssl_dir":          "/tmp",
				"application_name": "test-app",
			},
			want: "postgresql://root@localhost:26257?application_name=test-app&sslmode=enable&sslrootcert=/tmp/ca.crt&sslcert=/tmp/client.root.crt&sslkey=/tmp/client.root.key",
		},
		{
			name: "missing host",
			params: map[string]string{
				"port":     "26257",
				"user":     "root",
				"ssl_mode": "enable",
				"ssl_dir":  "/tmp",
			},
			want: "",
		},
		{
			name: "missing port",
			params: map[string]string{
				"host":     "localhost",
				"user":     "root",
				"ssl_mode": "enable",
				"ssl_dir":  "/tmp",
			},
			want: "",
		},
		{
			name: "missing user",
			params: map[string]string{
				"host":     "localhost",
				"port":     "26257",
				"ssl_mode": "enable",
				"ssl_dir":  "/tmp",
			},
			want: "",
		},
		{
			name: "missing ssl_mode",
			params: map[string]string{
				"host":    "localhost",
				"port":    "26257",
				"user":    "root",
				"ssl_dir": "/tmp",
			},
			want: "",
		},
		{
			name: "ssl_disabled",
			params: map[string]string{
				"host":     "localhost",
				"port":     "26257",
				"user":     "root",
				"ssl_mode": "disable",
			},
			want: "postgresql://root@localhost:26257?application_name=dss&sslmode=disable",
		},
		{
			name: "missing ssl_dir",
			params: map[string]string{
				"host":     "localhost",
				"port":     "26257",
				"user":     "root",
				"ssl_mode": "enable",
			},
			want: "",
		},
	}
	for _, c := range cases {
		got, _ := BuildURI(c.params)
		require.Equal(t, c.want, got)
	}
}
