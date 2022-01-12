// This file is auto-generated; do not change as any changes will be overwritten
package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"regexp"
)

func writeJson(w http.ResponseWriter, code int, obj interface{}) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(code)
	if err := json.NewEncoder(w).Encode(obj); err != nil {
		io.WriteString(w, fmt.Sprintf("{\"error_message\": \"Error encoding JSON: %s\"}", err.Error()))
	}
}

func (s *APIRouter) QueryOperationalIntentReferences(exp *regexp.Regexp, w http.ResponseWriter, r *http.Request) {
	var req QueryOperationalIntentReferencesRequest

	// Authorize request
	req.Auth = s.Authorizer.Authorize(w, r, &QueryOperationalIntentReferencesSecurity)

	// Parse request body
	req.Body = new(QueryOperationalIntentReferenceParameters)
	defer r.Body.Close()
	req.BodyParseError = json.NewDecoder(r.Body).Decode(req.Body)

	// Call implementation
	response := s.Implementation.QueryOperationalIntentReferences(&req)

	// Write response to client
	if response.Response200 != nil {
		writeJson(w, 200, response.Response200)
		return
	}
	if response.Response400 != nil {
		writeJson(w, 400, response.Response400)
		return
	}
	if response.Response401 != nil {
		writeJson(w, 401, response.Response401)
		return
	}
	if response.Response403 != nil {
		writeJson(w, 403, response.Response403)
		return
	}
	if response.Response413 != nil {
		writeJson(w, 413, response.Response413)
		return
	}
	if response.Response429 != nil {
		writeJson(w, 429, response.Response429)
		return
	}
	if response.Response500 != nil {
		writeJson(w, 500, response.Response500)
		return
	}
	writeJson(w, 500, InternalServerErrorBody{"Handler implementation did not set a response"})
}

func (s *APIRouter) GetOperationalIntentReference(exp *regexp.Regexp, w http.ResponseWriter, r *http.Request) {
	var req GetOperationalIntentReferenceRequest

	// Authorize request
	req.Auth = s.Authorizer.Authorize(w, r, &GetOperationalIntentReferenceSecurity)

	// Parse path parameters
	pathMatch := exp.FindStringSubmatch(r.URL.Path)
	req.Entityid = EntityID(pathMatch[1])

	// Call implementation
	response := s.Implementation.GetOperationalIntentReference(&req)

	// Write response to client
	if response.Response200 != nil {
		writeJson(w, 200, response.Response200)
		return
	}
	if response.Response400 != nil {
		writeJson(w, 400, response.Response400)
		return
	}
	if response.Response401 != nil {
		writeJson(w, 401, response.Response401)
		return
	}
	if response.Response403 != nil {
		writeJson(w, 403, response.Response403)
		return
	}
	if response.Response404 != nil {
		writeJson(w, 404, response.Response404)
		return
	}
	if response.Response429 != nil {
		writeJson(w, 429, response.Response429)
		return
	}
	if response.Response500 != nil {
		writeJson(w, 500, response.Response500)
		return
	}
	writeJson(w, 500, InternalServerErrorBody{"Handler implementation did not set a response"})
}

func (s *APIRouter) CreateOperationalIntentReference(exp *regexp.Regexp, w http.ResponseWriter, r *http.Request) {
	var req CreateOperationalIntentReferenceRequest

	// Authorize request
	req.Auth = s.Authorizer.Authorize(w, r, &CreateOperationalIntentReferenceSecurity)

	// Parse path parameters
	pathMatch := exp.FindStringSubmatch(r.URL.Path)
	req.Entityid = EntityID(pathMatch[1])

	// Parse request body
	req.Body = new(PutOperationalIntentReferenceParameters)
	defer r.Body.Close()
	req.BodyParseError = json.NewDecoder(r.Body).Decode(req.Body)

	// Call implementation
	response := s.Implementation.CreateOperationalIntentReference(&req)

	// Write response to client
	if response.Response201 != nil {
		writeJson(w, 201, response.Response201)
		return
	}
	if response.Response400 != nil {
		writeJson(w, 400, response.Response400)
		return
	}
	if response.Response401 != nil {
		writeJson(w, 401, response.Response401)
		return
	}
	if response.Response403 != nil {
		writeJson(w, 403, response.Response403)
		return
	}
	if response.Response409 != nil {
		writeJson(w, 409, response.Response409)
		return
	}
	if response.Response412 != nil {
		writeJson(w, 412, response.Response412)
		return
	}
	if response.Response413 != nil {
		writeJson(w, 413, response.Response413)
		return
	}
	if response.Response429 != nil {
		writeJson(w, 429, response.Response429)
		return
	}
	if response.Response500 != nil {
		writeJson(w, 500, response.Response500)
		return
	}
	writeJson(w, 500, InternalServerErrorBody{"Handler implementation did not set a response"})
}

func (s *APIRouter) UpdateOperationalIntentReference(exp *regexp.Regexp, w http.ResponseWriter, r *http.Request) {
	var req UpdateOperationalIntentReferenceRequest

	// Authorize request
	req.Auth = s.Authorizer.Authorize(w, r, &UpdateOperationalIntentReferenceSecurity)

	// Parse path parameters
	pathMatch := exp.FindStringSubmatch(r.URL.Path)
	req.Entityid = EntityID(pathMatch[1])
	req.Ovn = EntityOVN(pathMatch[2])

	// Parse request body
	req.Body = new(PutOperationalIntentReferenceParameters)
	defer r.Body.Close()
	req.BodyParseError = json.NewDecoder(r.Body).Decode(req.Body)

	// Call implementation
	response := s.Implementation.UpdateOperationalIntentReference(&req)

	// Write response to client
	if response.Response200 != nil {
		writeJson(w, 200, response.Response200)
		return
	}
	if response.Response400 != nil {
		writeJson(w, 400, response.Response400)
		return
	}
	if response.Response401 != nil {
		writeJson(w, 401, response.Response401)
		return
	}
	if response.Response403 != nil {
		writeJson(w, 403, response.Response403)
		return
	}
	if response.Response409 != nil {
		writeJson(w, 409, response.Response409)
		return
	}
	if response.Response412 != nil {
		writeJson(w, 412, response.Response412)
		return
	}
	if response.Response413 != nil {
		writeJson(w, 413, response.Response413)
		return
	}
	if response.Response429 != nil {
		writeJson(w, 429, response.Response429)
		return
	}
	if response.Response500 != nil {
		writeJson(w, 500, response.Response500)
		return
	}
	writeJson(w, 500, InternalServerErrorBody{"Handler implementation did not set a response"})
}

func (s *APIRouter) DeleteOperationalIntentReference(exp *regexp.Regexp, w http.ResponseWriter, r *http.Request) {
	var req DeleteOperationalIntentReferenceRequest

	// Authorize request
	req.Auth = s.Authorizer.Authorize(w, r, &DeleteOperationalIntentReferenceSecurity)

	// Parse path parameters
	pathMatch := exp.FindStringSubmatch(r.URL.Path)
	req.Entityid = EntityID(pathMatch[1])
	req.Ovn = EntityOVN(pathMatch[2])

	// Call implementation
	response := s.Implementation.DeleteOperationalIntentReference(&req)

	// Write response to client
	if response.Response200 != nil {
		writeJson(w, 200, response.Response200)
		return
	}
	if response.Response400 != nil {
		writeJson(w, 400, response.Response400)
		return
	}
	if response.Response401 != nil {
		writeJson(w, 401, response.Response401)
		return
	}
	if response.Response403 != nil {
		writeJson(w, 403, response.Response403)
		return
	}
	if response.Response404 != nil {
		writeJson(w, 404, response.Response404)
		return
	}
	if response.Response409 != nil {
		writeJson(w, 409, response.Response409)
		return
	}
	if response.Response412 != nil {
		writeJson(w, 412, response.Response412)
		return
	}
	if response.Response429 != nil {
		writeJson(w, 429, response.Response429)
		return
	}
	if response.Response500 != nil {
		writeJson(w, 500, response.Response500)
		return
	}
	writeJson(w, 500, InternalServerErrorBody{"Handler implementation did not set a response"})
}

func (s *APIRouter) QueryConstraintReferences(exp *regexp.Regexp, w http.ResponseWriter, r *http.Request) {
	var req QueryConstraintReferencesRequest

	// Authorize request
	req.Auth = s.Authorizer.Authorize(w, r, &QueryConstraintReferencesSecurity)

	// Parse request body
	req.Body = new(QueryConstraintReferenceParameters)
	defer r.Body.Close()
	req.BodyParseError = json.NewDecoder(r.Body).Decode(req.Body)

	// Call implementation
	response := s.Implementation.QueryConstraintReferences(&req)

	// Write response to client
	if response.Response200 != nil {
		writeJson(w, 200, response.Response200)
		return
	}
	if response.Response400 != nil {
		writeJson(w, 400, response.Response400)
		return
	}
	if response.Response401 != nil {
		writeJson(w, 401, response.Response401)
		return
	}
	if response.Response403 != nil {
		writeJson(w, 403, response.Response403)
		return
	}
	if response.Response413 != nil {
		writeJson(w, 413, response.Response413)
		return
	}
	if response.Response429 != nil {
		writeJson(w, 429, response.Response429)
		return
	}
	if response.Response500 != nil {
		writeJson(w, 500, response.Response500)
		return
	}
	writeJson(w, 500, InternalServerErrorBody{"Handler implementation did not set a response"})
}

func (s *APIRouter) GetConstraintReference(exp *regexp.Regexp, w http.ResponseWriter, r *http.Request) {
	var req GetConstraintReferenceRequest

	// Authorize request
	req.Auth = s.Authorizer.Authorize(w, r, &GetConstraintReferenceSecurity)

	// Parse path parameters
	pathMatch := exp.FindStringSubmatch(r.URL.Path)
	req.Entityid = EntityID(pathMatch[1])

	// Call implementation
	response := s.Implementation.GetConstraintReference(&req)

	// Write response to client
	if response.Response200 != nil {
		writeJson(w, 200, response.Response200)
		return
	}
	if response.Response400 != nil {
		writeJson(w, 400, response.Response400)
		return
	}
	if response.Response401 != nil {
		writeJson(w, 401, response.Response401)
		return
	}
	if response.Response403 != nil {
		writeJson(w, 403, response.Response403)
		return
	}
	if response.Response404 != nil {
		writeJson(w, 404, response.Response404)
		return
	}
	if response.Response429 != nil {
		writeJson(w, 429, response.Response429)
		return
	}
	if response.Response500 != nil {
		writeJson(w, 500, response.Response500)
		return
	}
	writeJson(w, 500, InternalServerErrorBody{"Handler implementation did not set a response"})
}

func (s *APIRouter) CreateConstraintReference(exp *regexp.Regexp, w http.ResponseWriter, r *http.Request) {
	var req CreateConstraintReferenceRequest

	// Authorize request
	req.Auth = s.Authorizer.Authorize(w, r, &CreateConstraintReferenceSecurity)

	// Parse path parameters
	pathMatch := exp.FindStringSubmatch(r.URL.Path)
	req.Entityid = EntityID(pathMatch[1])

	// Parse request body
	req.Body = new(PutConstraintReferenceParameters)
	defer r.Body.Close()
	req.BodyParseError = json.NewDecoder(r.Body).Decode(req.Body)

	// Call implementation
	response := s.Implementation.CreateConstraintReference(&req)

	// Write response to client
	if response.Response201 != nil {
		writeJson(w, 201, response.Response201)
		return
	}
	if response.Response400 != nil {
		writeJson(w, 400, response.Response400)
		return
	}
	if response.Response401 != nil {
		writeJson(w, 401, response.Response401)
		return
	}
	if response.Response403 != nil {
		writeJson(w, 403, response.Response403)
		return
	}
	if response.Response409 != nil {
		writeJson(w, 409, response.Response409)
		return
	}
	if response.Response413 != nil {
		writeJson(w, 413, response.Response413)
		return
	}
	if response.Response429 != nil {
		writeJson(w, 429, response.Response429)
		return
	}
	if response.Response500 != nil {
		writeJson(w, 500, response.Response500)
		return
	}
	writeJson(w, 500, InternalServerErrorBody{"Handler implementation did not set a response"})
}

func (s *APIRouter) UpdateConstraintReference(exp *regexp.Regexp, w http.ResponseWriter, r *http.Request) {
	var req UpdateConstraintReferenceRequest

	// Authorize request
	req.Auth = s.Authorizer.Authorize(w, r, &UpdateConstraintReferenceSecurity)

	// Parse path parameters
	pathMatch := exp.FindStringSubmatch(r.URL.Path)
	req.Entityid = EntityID(pathMatch[1])
	req.Ovn = EntityOVN(pathMatch[2])

	// Parse request body
	req.Body = new(PutConstraintReferenceParameters)
	defer r.Body.Close()
	req.BodyParseError = json.NewDecoder(r.Body).Decode(req.Body)

	// Call implementation
	response := s.Implementation.UpdateConstraintReference(&req)

	// Write response to client
	if response.Response200 != nil {
		writeJson(w, 200, response.Response200)
		return
	}
	if response.Response400 != nil {
		writeJson(w, 400, response.Response400)
		return
	}
	if response.Response401 != nil {
		writeJson(w, 401, response.Response401)
		return
	}
	if response.Response403 != nil {
		writeJson(w, 403, response.Response403)
		return
	}
	if response.Response409 != nil {
		writeJson(w, 409, response.Response409)
		return
	}
	if response.Response413 != nil {
		writeJson(w, 413, response.Response413)
		return
	}
	if response.Response429 != nil {
		writeJson(w, 429, response.Response429)
		return
	}
	if response.Response500 != nil {
		writeJson(w, 500, response.Response500)
		return
	}
	writeJson(w, 500, InternalServerErrorBody{"Handler implementation did not set a response"})
}

func (s *APIRouter) DeleteConstraintReference(exp *regexp.Regexp, w http.ResponseWriter, r *http.Request) {
	var req DeleteConstraintReferenceRequest

	// Authorize request
	req.Auth = s.Authorizer.Authorize(w, r, &DeleteConstraintReferenceSecurity)

	// Parse path parameters
	pathMatch := exp.FindStringSubmatch(r.URL.Path)
	req.Entityid = EntityID(pathMatch[1])
	req.Ovn = EntityOVN(pathMatch[2])

	// Call implementation
	response := s.Implementation.DeleteConstraintReference(&req)

	// Write response to client
	if response.Response200 != nil {
		writeJson(w, 200, response.Response200)
		return
	}
	if response.Response400 != nil {
		writeJson(w, 400, response.Response400)
		return
	}
	if response.Response401 != nil {
		writeJson(w, 401, response.Response401)
		return
	}
	if response.Response403 != nil {
		writeJson(w, 403, response.Response403)
		return
	}
	if response.Response404 != nil {
		writeJson(w, 404, response.Response404)
		return
	}
	if response.Response409 != nil {
		writeJson(w, 409, response.Response409)
		return
	}
	if response.Response429 != nil {
		writeJson(w, 429, response.Response429)
		return
	}
	if response.Response500 != nil {
		writeJson(w, 500, response.Response500)
		return
	}
	writeJson(w, 500, InternalServerErrorBody{"Handler implementation did not set a response"})
}

func (s *APIRouter) QuerySubscriptions(exp *regexp.Regexp, w http.ResponseWriter, r *http.Request) {
	var req QuerySubscriptionsRequest

	// Authorize request
	req.Auth = s.Authorizer.Authorize(w, r, &QuerySubscriptionsSecurity)

	// Parse request body
	req.Body = new(QuerySubscriptionParameters)
	defer r.Body.Close()
	req.BodyParseError = json.NewDecoder(r.Body).Decode(req.Body)

	// Call implementation
	response := s.Implementation.QuerySubscriptions(&req)

	// Write response to client
	if response.Response200 != nil {
		writeJson(w, 200, response.Response200)
		return
	}
	if response.Response400 != nil {
		writeJson(w, 400, response.Response400)
		return
	}
	if response.Response401 != nil {
		writeJson(w, 401, response.Response401)
		return
	}
	if response.Response403 != nil {
		writeJson(w, 403, response.Response403)
		return
	}
	if response.Response413 != nil {
		writeJson(w, 413, response.Response413)
		return
	}
	if response.Response429 != nil {
		writeJson(w, 429, response.Response429)
		return
	}
	if response.Response500 != nil {
		writeJson(w, 500, response.Response500)
		return
	}
	writeJson(w, 500, InternalServerErrorBody{"Handler implementation did not set a response"})
}

func (s *APIRouter) GetSubscription(exp *regexp.Regexp, w http.ResponseWriter, r *http.Request) {
	var req GetSubscriptionRequest

	// Authorize request
	req.Auth = s.Authorizer.Authorize(w, r, &GetSubscriptionSecurity)

	// Parse path parameters
	pathMatch := exp.FindStringSubmatch(r.URL.Path)
	req.Subscriptionid = SubscriptionID(pathMatch[1])

	// Call implementation
	response := s.Implementation.GetSubscription(&req)

	// Write response to client
	if response.Response200 != nil {
		writeJson(w, 200, response.Response200)
		return
	}
	if response.Response400 != nil {
		writeJson(w, 400, response.Response400)
		return
	}
	if response.Response401 != nil {
		writeJson(w, 401, response.Response401)
		return
	}
	if response.Response403 != nil {
		writeJson(w, 403, response.Response403)
		return
	}
	if response.Response404 != nil {
		writeJson(w, 404, response.Response404)
		return
	}
	if response.Response429 != nil {
		writeJson(w, 429, response.Response429)
		return
	}
	if response.Response500 != nil {
		writeJson(w, 500, response.Response500)
		return
	}
	writeJson(w, 500, InternalServerErrorBody{"Handler implementation did not set a response"})
}

func (s *APIRouter) CreateSubscription(exp *regexp.Regexp, w http.ResponseWriter, r *http.Request) {
	var req CreateSubscriptionRequest

	// Authorize request
	req.Auth = s.Authorizer.Authorize(w, r, &CreateSubscriptionSecurity)

	// Parse path parameters
	pathMatch := exp.FindStringSubmatch(r.URL.Path)
	req.Subscriptionid = SubscriptionID(pathMatch[1])

	// Parse request body
	req.Body = new(PutSubscriptionParameters)
	defer r.Body.Close()
	req.BodyParseError = json.NewDecoder(r.Body).Decode(req.Body)

	// Call implementation
	response := s.Implementation.CreateSubscription(&req)

	// Write response to client
	if response.Response200 != nil {
		writeJson(w, 200, response.Response200)
		return
	}
	if response.Response400 != nil {
		writeJson(w, 400, response.Response400)
		return
	}
	if response.Response401 != nil {
		writeJson(w, 401, response.Response401)
		return
	}
	if response.Response403 != nil {
		writeJson(w, 403, response.Response403)
		return
	}
	if response.Response409 != nil {
		writeJson(w, 409, response.Response409)
		return
	}
	if response.Response429 != nil {
		writeJson(w, 429, response.Response429)
		return
	}
	if response.Response500 != nil {
		writeJson(w, 500, response.Response500)
		return
	}
	writeJson(w, 500, InternalServerErrorBody{"Handler implementation did not set a response"})
}

func (s *APIRouter) UpdateSubscription(exp *regexp.Regexp, w http.ResponseWriter, r *http.Request) {
	var req UpdateSubscriptionRequest

	// Authorize request
	req.Auth = s.Authorizer.Authorize(w, r, &UpdateSubscriptionSecurity)

	// Parse path parameters
	pathMatch := exp.FindStringSubmatch(r.URL.Path)
	req.Subscriptionid = SubscriptionID(pathMatch[1])
	req.Version = pathMatch[2]

	// Parse request body
	req.Body = new(PutSubscriptionParameters)
	defer r.Body.Close()
	req.BodyParseError = json.NewDecoder(r.Body).Decode(req.Body)

	// Call implementation
	response := s.Implementation.UpdateSubscription(&req)

	// Write response to client
	if response.Response200 != nil {
		writeJson(w, 200, response.Response200)
		return
	}
	if response.Response400 != nil {
		writeJson(w, 400, response.Response400)
		return
	}
	if response.Response401 != nil {
		writeJson(w, 401, response.Response401)
		return
	}
	if response.Response403 != nil {
		writeJson(w, 403, response.Response403)
		return
	}
	if response.Response409 != nil {
		writeJson(w, 409, response.Response409)
		return
	}
	if response.Response429 != nil {
		writeJson(w, 429, response.Response429)
		return
	}
	if response.Response500 != nil {
		writeJson(w, 500, response.Response500)
		return
	}
	writeJson(w, 500, InternalServerErrorBody{"Handler implementation did not set a response"})
}

func (s *APIRouter) DeleteSubscription(exp *regexp.Regexp, w http.ResponseWriter, r *http.Request) {
	var req DeleteSubscriptionRequest

	// Authorize request
	req.Auth = s.Authorizer.Authorize(w, r, &DeleteSubscriptionSecurity)

	// Parse path parameters
	pathMatch := exp.FindStringSubmatch(r.URL.Path)
	req.Subscriptionid = SubscriptionID(pathMatch[1])
	req.Version = pathMatch[2]

	// Call implementation
	response := s.Implementation.DeleteSubscription(&req)

	// Write response to client
	if response.Response200 != nil {
		writeJson(w, 200, response.Response200)
		return
	}
	if response.Response400 != nil {
		writeJson(w, 400, response.Response400)
		return
	}
	if response.Response401 != nil {
		writeJson(w, 401, response.Response401)
		return
	}
	if response.Response403 != nil {
		writeJson(w, 403, response.Response403)
		return
	}
	if response.Response404 != nil {
		writeJson(w, 404, response.Response404)
		return
	}
	if response.Response409 != nil {
		writeJson(w, 409, response.Response409)
		return
	}
	if response.Response429 != nil {
		writeJson(w, 429, response.Response429)
		return
	}
	if response.Response500 != nil {
		writeJson(w, 500, response.Response500)
		return
	}
	writeJson(w, 500, InternalServerErrorBody{"Handler implementation did not set a response"})
}

func (s *APIRouter) MakeDssReport(exp *regexp.Regexp, w http.ResponseWriter, r *http.Request) {
	var req MakeDssReportRequest

	// Authorize request
	req.Auth = s.Authorizer.Authorize(w, r, &MakeDssReportSecurity)

	// Parse request body
	req.Body = new(ErrorReport)
	defer r.Body.Close()
	req.BodyParseError = json.NewDecoder(r.Body).Decode(req.Body)

	// Call implementation
	response := s.Implementation.MakeDssReport(&req)

	// Write response to client
	if response.Response201 != nil {
		writeJson(w, 201, response.Response201)
		return
	}
	if response.Response400 != nil {
		writeJson(w, 400, response.Response400)
		return
	}
	if response.Response401 != nil {
		writeJson(w, 401, response.Response401)
		return
	}
	if response.Response403 != nil {
		writeJson(w, 403, response.Response403)
		return
	}
	if response.Response429 != nil {
		writeJson(w, 429, response.Response429)
		return
	}
	if response.Response500 != nil {
		writeJson(w, 500, response.Response500)
		return
	}
	writeJson(w, 500, InternalServerErrorBody{"Handler implementation did not set a response"})
}

func (s *APIRouter) GetUssAvailability(exp *regexp.Regexp, w http.ResponseWriter, r *http.Request) {
	var req GetUssAvailabilityRequest

	// Authorize request
	req.Auth = s.Authorizer.Authorize(w, r, &GetUssAvailabilitySecurity)

	// Parse path parameters
	pathMatch := exp.FindStringSubmatch(r.URL.Path)
	req.Uss_id = pathMatch[1]

	// Call implementation
	response := s.Implementation.GetUssAvailability(&req)

	// Write response to client
	if response.Response200 != nil {
		writeJson(w, 200, response.Response200)
		return
	}
	if response.Response400 != nil {
		writeJson(w, 400, response.Response400)
		return
	}
	if response.Response401 != nil {
		writeJson(w, 401, response.Response401)
		return
	}
	if response.Response403 != nil {
		writeJson(w, 403, response.Response403)
		return
	}
	if response.Response429 != nil {
		writeJson(w, 429, response.Response429)
		return
	}
	if response.Response500 != nil {
		writeJson(w, 500, response.Response500)
		return
	}
	writeJson(w, 500, InternalServerErrorBody{"Handler implementation did not set a response"})
}

func (s *APIRouter) SetUssAvailability(exp *regexp.Regexp, w http.ResponseWriter, r *http.Request) {
	var req SetUssAvailabilityRequest

	// Authorize request
	req.Auth = s.Authorizer.Authorize(w, r, &SetUssAvailabilitySecurity)

	// Parse path parameters
	pathMatch := exp.FindStringSubmatch(r.URL.Path)
	req.Uss_id = pathMatch[1]

	// Parse request body
	req.Body = new(SetUssAvailabilityStatusParameters)
	defer r.Body.Close()
	req.BodyParseError = json.NewDecoder(r.Body).Decode(req.Body)

	// Call implementation
	response := s.Implementation.SetUssAvailability(&req)

	// Write response to client
	if response.Response200 != nil {
		writeJson(w, 200, response.Response200)
		return
	}
	if response.Response400 != nil {
		writeJson(w, 400, response.Response400)
		return
	}
	if response.Response401 != nil {
		writeJson(w, 401, response.Response401)
		return
	}
	if response.Response403 != nil {
		writeJson(w, 403, response.Response403)
		return
	}
	if response.Response429 != nil {
		writeJson(w, 429, response.Response429)
		return
	}
	if response.Response500 != nil {
		writeJson(w, 500, response.Response500)
		return
	}
	writeJson(w, 500, InternalServerErrorBody{"Handler implementation did not set a response"})
}

func MakeAPIRouter(impl Implementation, auth Authorizer) APIRouter {
	router := APIRouter{Implementation: impl, Authorizer: auth, Routes: make([]*Route, 18)}

	pattern := regexp.MustCompile("^/scd/dss/v1/operational_intent_references/query$")
	router.Routes[0] = &Route{Pattern: pattern, Handler: router.QueryOperationalIntentReferences}

	pattern = regexp.MustCompile("^/scd/dss/v1/operational_intent_references/(?P<entityid>[^/]*)$")
	router.Routes[1] = &Route{Pattern: pattern, Handler: router.GetOperationalIntentReference}

	pattern = regexp.MustCompile("^/scd/dss/v1/operational_intent_references/(?P<entityid>[^/]*)$")
	router.Routes[2] = &Route{Pattern: pattern, Handler: router.CreateOperationalIntentReference}

	pattern = regexp.MustCompile("^/scd/dss/v1/operational_intent_references/(?P<entityid>[^/]*)/(?P<ovn>[^/]*)$")
	router.Routes[3] = &Route{Pattern: pattern, Handler: router.UpdateOperationalIntentReference}

	pattern = regexp.MustCompile("^/scd/dss/v1/operational_intent_references/(?P<entityid>[^/]*)/(?P<ovn>[^/]*)$")
	router.Routes[4] = &Route{Pattern: pattern, Handler: router.DeleteOperationalIntentReference}

	pattern = regexp.MustCompile("^/scd/dss/v1/constraint_references/query$")
	router.Routes[5] = &Route{Pattern: pattern, Handler: router.QueryConstraintReferences}

	pattern = regexp.MustCompile("^/scd/dss/v1/constraint_references/(?P<entityid>[^/]*)$")
	router.Routes[6] = &Route{Pattern: pattern, Handler: router.GetConstraintReference}

	pattern = regexp.MustCompile("^/scd/dss/v1/constraint_references/(?P<entityid>[^/]*)$")
	router.Routes[7] = &Route{Pattern: pattern, Handler: router.CreateConstraintReference}

	pattern = regexp.MustCompile("^/scd/dss/v1/constraint_references/(?P<entityid>[^/]*)/(?P<ovn>[^/]*)$")
	router.Routes[8] = &Route{Pattern: pattern, Handler: router.UpdateConstraintReference}

	pattern = regexp.MustCompile("^/scd/dss/v1/constraint_references/(?P<entityid>[^/]*)/(?P<ovn>[^/]*)$")
	router.Routes[9] = &Route{Pattern: pattern, Handler: router.DeleteConstraintReference}

	pattern = regexp.MustCompile("^/scd/dss/v1/subscriptions/query$")
	router.Routes[10] = &Route{Pattern: pattern, Handler: router.QuerySubscriptions}

	pattern = regexp.MustCompile("^/scd/dss/v1/subscriptions/(?P<subscriptionid>[^/]*)$")
	router.Routes[11] = &Route{Pattern: pattern, Handler: router.GetSubscription}

	pattern = regexp.MustCompile("^/scd/dss/v1/subscriptions/(?P<subscriptionid>[^/]*)$")
	router.Routes[12] = &Route{Pattern: pattern, Handler: router.CreateSubscription}

	pattern = regexp.MustCompile("^/scd/dss/v1/subscriptions/(?P<subscriptionid>[^/]*)/(?P<version>[^/]*)$")
	router.Routes[13] = &Route{Pattern: pattern, Handler: router.UpdateSubscription}

	pattern = regexp.MustCompile("^/scd/dss/v1/subscriptions/(?P<subscriptionid>[^/]*)/(?P<version>[^/]*)$")
	router.Routes[14] = &Route{Pattern: pattern, Handler: router.DeleteSubscription}

	pattern = regexp.MustCompile("^/scd/dss/v1/reports$")
	router.Routes[15] = &Route{Pattern: pattern, Handler: router.MakeDssReport}

	pattern = regexp.MustCompile("^/scd/dss/v1/uss_availability/(?P<uss_id>[^/]*)$")
	router.Routes[16] = &Route{Pattern: pattern, Handler: router.GetUssAvailability}

	pattern = regexp.MustCompile("^/scd/dss/v1/uss_availability/(?P<uss_id>[^/]*)$")
	router.Routes[17] = &Route{Pattern: pattern, Handler: router.SetUssAvailability}

	return router
}
