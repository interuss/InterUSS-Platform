package scd

import (
	"context"

	"github.com/golang/geo/s2"
	dssmodels "github.com/interuss/dss/pkg/dss/models"
	scdmodels "github.com/interuss/dss/pkg/dss/scd/models"
)

// Store abstracts interactions with a backing data store.
type Store interface {
	// SearchSubscriptions returns all Subscriptions owned by "owner" in "cells".
	SearchSubscriptions(ctx context.Context, cells s2.CellUnion, owner dssmodels.Owner) ([]*scdmodels.Subscription, error)

	// GetSubscription returns the Subscription referenced by id, or nil if the
	// Subscription doesn't exist
	GetSubscription(ctx context.Context, id scdmodels.ID, owner dssmodels.Owner) (*scdmodels.Subscription, error)

	// UpsertSubscription upserts sub into the store and returns the result
	// subscription.
	UpsertSubscription(ctx context.Context, sub *scdmodels.Subscription) (*scdmodels.Subscription, error)

	// DeleteSubscription deletes a Subscription from the store and returns the
	// deleted subscription.  Returns nil and an error if the Subscription does
	// not exist, or is owned by someone other than the specified owner.
	DeleteSubscription(ctx context.Context, id scdmodels.ID, owner dssmodels.Owner, version scdmodels.Version) (*scdmodels.Subscription, error)
}

// DummyStore implements Store interface entirely with error-free no-ops
type DummyStore struct {
}

// MakeDummySubscription returns a dummy subscription instance with ID id.
func MakeDummySubscription(id scdmodels.ID) *scdmodels.Subscription {
	altLo := float32(11235)
	altHi := float32(81321)
	result := &scdmodels.Subscription{
		ID:                   id,
		Version:              314,
		NotificationIndex:    123,
		BaseURL:              "https://exampleuss.com/utm",
		AltitudeLo:           &altLo,
		AltitudeHi:           &altHi,
		NotifyForOperations:  true,
		NotifyForConstraints: false,
		ImplicitSubscription: true,
		DependentOperations: []scdmodels.ID{
			scdmodels.ID("c09bcff5-35a4-41de-9220-6c140a9857ee"),
			scdmodels.ID("2cff1c62-cf1a-41ad-826b-d12dad432f21"),
		},
	}
	return result
}

func (s *DummyStore) SearchSubscriptions(ctx context.Context, cells s2.CellUnion, owner dssmodels.Owner) ([]*scdmodels.Subscription, error) {
	subs := []*scdmodels.Subscription{
		MakeDummySubscription(scdmodels.ID("444eab15-8384-4e39-8589-5161689aee56")),
	}
	return subs, nil
}

func (s *DummyStore) GetSubscription(ctx context.Context, id scdmodels.ID, owner dssmodels.Owner) (*scdmodels.Subscription, error) {
	return MakeDummySubscription(id), nil
}

func (s *DummyStore) UpsertSubscription(ctx context.Context, sub *scdmodels.Subscription) (*scdmodels.Subscription, error) {
	return sub, nil
}

func (s *DummyStore) DeleteSubscription(ctx context.Context, id scdmodels.ID, owner dssmodels.Owner, version scdmodels.Version) (*scdmodels.Subscription, error) {
	sub := MakeDummySubscription(id)
	sub.ID = id
	return sub, nil
}
