package scd

import (
	"context"
	"database/sql"
	"fmt"

	"github.com/golang/geo/s2"
	"github.com/interuss/dss/pkg/api/v1/scdpb"
	"github.com/interuss/dss/pkg/auth"
	dsserr "github.com/interuss/dss/pkg/errors"
	dssmodels "github.com/interuss/dss/pkg/models"
	scdmodels "github.com/interuss/dss/pkg/scd/models"
	"github.com/interuss/dss/pkg/scd/repos"
	"github.com/palantir/stacktrace"
)

func incrementNotificationIndices(ctx context.Context, r repos.Repository, subs []*scdmodels.Subscription) error {
	subIds := make([]dssmodels.ID, len(subs))
	for i, sub := range subs {
		subIds[i] = sub.ID
	}
	newIndices, err := r.IncrementNotificationIndices(ctx, subIds)
	if err != nil {
		return err
	}
	for i, newIndex := range newIndices {
		subs[i].NotificationIndex = newIndex
	}
	return nil
}

// DeleteConstraintReference deletes a single constraint ref for a given ID at
// the specified version.
func (a *Server) DeleteConstraintReference(ctx context.Context, req *scdpb.DeleteConstraintReferenceRequest) (*scdpb.ChangeConstraintReferenceResponse, error) {
	// Retrieve Constraint ID
	id, err := dssmodels.IDFromString(req.GetEntityuuid())
	if err != nil {
		return nil, dsserr.BadRequest("Invalid ID format")
	}

	// Retrieve ID of client making call
	owner, ok := auth.OwnerFromContext(ctx)
	if !ok {
		return nil, dsserr.PermissionDenied("missing owner from context")
	}

	var response *scdpb.ChangeConstraintReferenceResponse
	action := func(ctx context.Context, r repos.Repository) (err error) {
		// Make sure deletion request is valid
		old, err := r.GetConstraint(ctx, id)
		switch {
		case err == sql.ErrNoRows:
			return dsserr.NotFound(id.String())
		case err != nil:
			return err
		case old.Owner != owner:
			return dsserr.PermissionDenied(fmt.Sprintf("constraint is owned by %s", old.Owner))
		}

		// Find Subscriptions that may overlap the Constraint's Volume4D
		allsubs, err := r.SearchSubscriptions(ctx, &dssmodels.Volume4D{
			StartTime: old.StartTime,
			EndTime:   old.EndTime,
			SpatialVolume: &dssmodels.Volume3D{
				AltitudeHi: old.AltitudeUpper,
				AltitudeLo: old.AltitudeLower,
				Footprint: dssmodels.GeometryFunc(func() (s2.CellUnion, error) {
					return old.Cells, nil
				}),
			}})
		if err != nil {
			return err
		}

		// Limit Subscription notifications to only those interested in Constraints
		var subs []*scdmodels.Subscription
		for _, sub := range allsubs {
			if sub.NotifyForConstraints {
				subs = append(subs, sub)
			}
		}

		// Delete Constraint in Store
		err = r.DeleteConstraint(ctx, id)
		if err != nil {
			return err
		}

		// Increment notification indices for relevant Subscriptions
		err = incrementNotificationIndices(ctx, r, subs)
		if err != nil {
			return err
		}

		// Convert deleted Constraint to proto
		constraintProto, err := old.ToProto()
		if err != nil {
			return stacktrace.Propagate(err, "Could not convert Constraint to proto")
		}

		// Return response to client
		response = &scdpb.ChangeConstraintReferenceResponse{
			ConstraintReference: constraintProto,
			Subscribers:         makeSubscribersToNotify(subs),
		}

		return nil
	}

	err = a.Store.Transact(ctx, action)
	if err != nil {
		return nil, err
	}

	return response, nil
}

// GetConstraintReference returns a single constraint ref for the given ID.
func (a *Server) GetConstraintReference(ctx context.Context, req *scdpb.GetConstraintReferenceRequest) (*scdpb.GetConstraintReferenceResponse, error) {
	id, err := dssmodels.IDFromString(req.GetEntityuuid())
	if err != nil {
		return nil, dsserr.BadRequest("Invalid ID format")
	}

	owner, ok := auth.OwnerFromContext(ctx)
	if !ok {
		return nil, dsserr.PermissionDenied("missing owner from context")
	}

	var response *scdpb.GetConstraintReferenceResponse
	action := func(ctx context.Context, r repos.Repository) (err error) {
		constraint, err := r.GetConstraint(ctx, id)
		switch {
		case err == sql.ErrNoRows:
			return dsserr.NotFound(id.String())
		case err != nil:
			return err
		}

		if constraint.Owner != owner {
			constraint.OVN = scdmodels.OVN("")
		}

		// Convert retrieved Constraint to proto
		p, err := constraint.ToProto()
		if err != nil {
			return err
		}

		// Return response to client
		response = &scdpb.GetConstraintReferenceResponse{
			ConstraintReference: p,
		}

		return nil
	}

	err = a.Store.Transact(ctx, action)
	if err != nil {
		// TODO: wrap err in dss.Internal?
		return nil, err
	}

	return response, nil
}

// PutConstraintReference creates a single contraint ref.
func (a *Server) PutConstraintReference(ctx context.Context, req *scdpb.PutConstraintReferenceRequest) (*scdpb.ChangeConstraintReferenceResponse, error) {
	id, err := dssmodels.IDFromString(req.GetEntityuuid())
	if err != nil {
		return nil, dsserr.BadRequest("Invalid ID format")
	}

	// Retrieve ID of client making call
	owner, ok := auth.OwnerFromContext(ctx)
	if !ok {
		return nil, dsserr.PermissionDenied("missing owner from context")
	}

	var (
		params  = req.GetParams()
		extents = make([]*dssmodels.Volume4D, len(params.GetExtents()))
	)

	if len(params.UssBaseUrl) == 0 {
		return nil, dsserr.BadRequest("missing required UssBaseUrl")
	}

	// TODO: factor out logic below into common multi-vol4d parser and reuse with PutOperationReference
	for idx, extent := range params.GetExtents() {
		cExtent, err := dssmodels.Volume4DFromSCDProto(extent)
		if err != nil {
			return nil, dsserr.BadRequest(fmt.Sprintf("failed to parse extents: %s", err))
		}
		extents[idx] = cExtent
	}
	uExtent, err := dssmodels.UnionVolumes4D(extents...)
	if err != nil {
		return nil, dsserr.BadRequest(fmt.Sprintf("failed to union extents: %s", err))
	}

	if uExtent.StartTime == nil {
		return nil, dsserr.BadRequest("missing time_start from extents")
	}
	if uExtent.EndTime == nil {
		return nil, dsserr.BadRequest("missing time_end from extents")
	}

	cells, err := uExtent.CalculateSpatialCovering()
	if err != nil {
		return nil, dssErrorOfAreaError(err)
	}

	var response *scdpb.ChangeConstraintReferenceResponse
	action := func(ctx context.Context, r repos.Repository) (err error) {
		// Get existing Constraint, if any, and validate request
		old, err := r.GetConstraint(ctx, id)
		switch {
		case err == sql.ErrNoRows:
			// No existing Constraint; verify that creation was requested
			if params.OldVersion != 0 {
				return dsserr.VersionMismatch(fmt.Sprintf("old version %d does not exist", params.OldVersion))
			}
		case err != nil:
			return err
		}
		if old != nil {
			if old.Owner != owner {
				return dsserr.PermissionDenied(fmt.Sprintf("constraint is owned by %s", old.Owner))
			}
			if old.Version != scdmodels.Version(params.OldVersion) {
				return dsserr.VersionMismatch(fmt.Sprintf("version %d is not the current version", params.OldVersion))
			}
		}

		// Compute total affected Volume4D for notification purposes
		// TODO: Fix in Operations; Subscriptions should be pulled from both old and new 4D geometries
		var notifyVol4 *dssmodels.Volume4D
		if old == nil {
			notifyVol4 = uExtent
		} else {
			oldVol4 := &dssmodels.Volume4D{
				StartTime: old.StartTime,
				EndTime:   old.EndTime,
				SpatialVolume: &dssmodels.Volume3D{
					AltitudeHi: old.AltitudeUpper,
					AltitudeLo: old.AltitudeLower,
					Footprint: dssmodels.GeometryFunc(func() (s2.CellUnion, error) {
						return old.Cells, nil
					}),
				}}
			notifyVol4, err = dssmodels.UnionVolumes4D(uExtent, oldVol4)
			if err != nil {
				return err
			}
		}

		// Upsert the Constraint
		constraint, err := r.UpsertConstraint(ctx, &scdmodels.Constraint{
			ID:      id,
			Owner:   owner,
			Version: scdmodels.Version(params.OldVersion + 1),

			StartTime:     uExtent.StartTime,
			EndTime:       uExtent.EndTime,
			AltitudeLower: uExtent.SpatialVolume.AltitudeLo,
			AltitudeUpper: uExtent.SpatialVolume.AltitudeHi,

			USSBaseURL: params.UssBaseUrl,
			Cells:      cells,
		})
		if err != nil {
			return err
		}

		// Find Subscriptions that may need to be notified
		allsubs, err := r.SearchSubscriptions(ctx, notifyVol4)
		if err != nil {
			return err
		}

		// Limit Subscription notifications to only those interested in Constraints
		var subs []*scdmodels.Subscription
		for _, sub := range allsubs {
			if sub.NotifyForConstraints {
				subs = append(subs, sub)
			}
		}

		// Increment notification indices for relevant Subscriptions
		err = incrementNotificationIndices(ctx, r, subs)
		if err != nil {
			return err
		}

		// Convert upserted Constraint to proto
		p, err := constraint.ToProto()
		if err != nil {
			return err
		}

		// Return response to client
		response = &scdpb.ChangeConstraintReferenceResponse{
			ConstraintReference: p,
			Subscribers:         makeSubscribersToNotify(subs),
		}

		return nil
	}

	err = a.Store.Transact(ctx, action)
	if err != nil {
		// TODO: wrap err in dss.Internal?
		return nil, err
	}

	return response, nil
}

// QueryConstraintReferences queries existing contraint refs in the given
// bounds.
func (a *Server) QueryConstraintReferences(ctx context.Context, req *scdpb.QueryConstraintReferencesRequest) (*scdpb.SearchConstraintReferencesResponse, error) {
	// Retrieve the area of interest parameter
	aoi := req.GetParams().AreaOfInterest
	if aoi == nil {
		return nil, dsserr.BadRequest("missing area_of_interest")
	}

	// Parse area of interest to common Volume4D
	vol4, err := dssmodels.Volume4DFromSCDProto(aoi)
	if err != nil {
		return nil, err
	}

	// Retrieve ID of client making call
	owner, ok := auth.OwnerFromContext(ctx)
	if !ok {
		return nil, dsserr.PermissionDenied("missing owner from context")
	}

	var response *scdpb.SearchConstraintReferencesResponse
	action := func(ctx context.Context, r repos.Repository) (err error) {
		// Perform search query on Store
		constraints, err := r.SearchConstraints(ctx, vol4)
		if err != nil {
			return err
		}

		// Create response for client
		response = &scdpb.SearchConstraintReferencesResponse{}
		for _, constraint := range constraints {
			p, err := constraint.ToProto()
			if err != nil {
				return err
			}
			if constraint.Owner != owner {
				p.Ovn = ""
			}
			response.ConstraintReferences = append(response.ConstraintReferences, p)
		}

		return nil
	}

	err = a.Store.Transact(ctx, action)
	if err != nil {
		// TODO: wrap err in dss.Internal?
		return nil, err
	}

	return response, nil
}
