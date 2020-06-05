package aux

import (
	"context"
	"fmt"

	"github.com/interuss/dss/pkg/api/v1/auxpb"
	"github.com/interuss/dss/pkg/auth"
	dsserr "github.com/interuss/dss/pkg/errors"
	"github.com/interuss/dss/pkg/rid/server"
)

// Server implements auxpb.DSSAuxService.
type Server struct{}

// AuthScopes returns a map of endpoint to required Oauth scope.
func (a *Server) AuthScopes() map[auth.Operation]auth.KeyClaimedScopesValidator {
	return map[auth.Operation]auth.KeyClaimedScopesValidator{
		"/auxpb.DSSAuxService/ValidateOauth": auth.RequireAllScopes(server.Scopes.ISA.Write),
	}
}

// ValidateOauth will exercise validating the Oauth token
func (a *Server) ValidateOauth(ctx context.Context, req *auxpb.ValidateOauthRequest) (*auxpb.ValidateOauthResponse, error) {
	owner, ok := auth.OwnerFromContext(ctx)
	if !ok {
		return nil, dsserr.PermissionDenied("missing owner from context")
	}
	if req.Owner != "" && req.Owner != owner.String() {
		return nil, dsserr.PermissionDenied(fmt.Sprintf("owner mismatch, required: %s, but oauth token has %s", req.Owner, owner))
	}
	return &auxpb.ValidateOauthResponse{}, nil
}
