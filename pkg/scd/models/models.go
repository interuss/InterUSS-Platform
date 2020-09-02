package models

import (
	"crypto/sha256"
	"encoding/base64"
	"net/url"
	"time"

	"github.com/interuss/stacktrace"
)

type (
	// OVN models an opaque version number.
	OVN string

	// Version models the version of an entity.
	//
	// Primarily used as a fencing token in data mutations.
	Version int32
)

// NewOVNFromTime encodes t as an OVN.
func NewOVNFromTime(t time.Time, salt string) OVN {
	sum := sha256.Sum256([]byte(salt + t.Format(time.RFC3339)))
	return OVN(base64.StdEncoding.EncodeToString(
		sum[:],
	))
}

// Empty returns true if ovn indicates an empty opaque version number.
func (ovn OVN) Empty() bool {
	return len(ovn) == 0
}

// Valid returns true if ovn is valid.
func (ovn OVN) Valid() bool {
	return len(ovn) >= 16 && len(ovn) <= 128
}

func (ovn OVN) String() string {
	return string(ovn)
}

// Empty returns true if the value of v indicates an empty version.
func (v Version) Empty() bool {
	return v <= 0
}

// Matches returns true if v matches w.
func (v Version) Matches(w Version) bool {
	return v == w
}

// ValidateUSSBaseURL ensures https
func ValidateUSSBaseURL(s string) error {
	u, err := url.Parse(s)
	if err != nil {
		return stacktrace.Propagate(err, "Error parsing URL")
	}

	switch u.Scheme {
	case "https":
		// All good, proceed normally.
	case "http":
		return stacktrace.NewError("uss_base_url in new_subscription must use TLS")
	default:
		return stacktrace.NewError("uss_base_url must support https scheme")
	}

	return nil
}
