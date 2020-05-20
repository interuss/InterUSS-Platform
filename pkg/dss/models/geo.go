package models

import (
	"errors"
	"fmt"
	"time"

	"github.com/golang/geo/s2"
	"github.com/golang/protobuf/ptypes"
	"github.com/interuss/dss/pkg/dss/geo"
	"google.golang.org/protobuf/proto"

	// TODO: all of the uses of ridpb should use protos that can be used
	// by both rid and scd.
	"github.com/interuss/dss/pkg/api/v1/ridpb"
	"github.com/interuss/dss/pkg/api/v1/scdpb"
)

const (
	// TimeFormatRFC3339 is the string used for RFC3339
	TimeFormatRFC3339 = "RFC3339"
	minLat            = -90.0
	maxLat            = 90.0
	minLng            = -180.0
	maxLng            = 180.0
)

var (
	// ErrMissingSpatialVolume indicates that a spatial volume is required but
	// missing to complete an operation.
	ErrMissingSpatialVolume = errors.New("missing spatial volume")
	// ErrMissingFootprint indicates that a geometry footprint is required but
	// missing to complete an operation.
	ErrMissingFootprint = errors.New("missing footprint")

	errNotEnoughPointsInPolygon = errors.New("not enough points in polygon")
	errBadCoordSet              = errors.New("coordinates did not create a well formed area")
	errRadiusMustBeLargerThan0  = errors.New("radius must be larger than 0")

	unitToMeterMultiplicativeFactors = map[unit]float32{
		unitMeter: 1,
	}

	altitudeReferenceWGS84 altitudeReference = "W84"
	unitMeter              unit              = "M"
)

type (
	altitudeReference string
	unit              string
)

func (ar altitudeReference) String() string {
	return string(ar)
}

func (u unit) String() string {
	return string(u)
}

func float32p(v float32) *float32 {
	return &v
}

func timeP(t time.Time) *time.Time {
	if t.IsZero() {
		return nil
	}
	return &t
}

// Volume4D is a Contiguous block of geographic spacetime.
type Volume4D struct {
	// Constant spatial extent of this volume.
	SpatialVolume *Volume3D
	// End time of this volume.
	EndTime *time.Time
	// Beginning time of this volume.
	StartTime *time.Time
}

// Volume3D is A three-dimensional geographic volume consisting of a vertically-extruded shape.
type Volume3D struct {
	// Maximum bounding altitude (meters above the WGS84 ellipsoid) of this volume.
	AltitudeHi *float32
	// Minimum bounding altitude (meters above the WGS84 ellipsoid) of this volume.
	AltitudeLo *float32
	// Projection of this volume onto the earth's surface.
	Footprint Geometry
}

// Geometry models a geometry.
type Geometry interface {
	// CalculateCovering returns an s2 cell covering for a geometry.
	CalculateCovering() (s2.CellUnion, error)
}

// GeometryFunc is an implementation of Geometry
type GeometryFunc func() (s2.CellUnion, error)

type precomputedCellGeometry map[s2.CellID]struct{}

func (pcg precomputedCellGeometry) merge(ids ...s2.CellID) precomputedCellGeometry {
	for _, id := range ids {
		pcg[id] = struct{}{}
	}
	return pcg
}

func (pcg precomputedCellGeometry) CalculateCovering() (s2.CellUnion, error) {
	var (
		result = make(s2.CellUnion, len(pcg))
		idx    int
	)

	for id := range pcg {
		result[idx] = id
		idx++
	}

	return result, nil
}

// UnionVolumes4D unions volumes and returns a volume that covers all the
// individual volumes in space and time.
func UnionVolumes4D(volumes ...*Volume4D) (*Volume4D, error) {
	result := &Volume4D{}

	for _, volume := range volumes {
		if volume.EndTime != nil {
			if result.EndTime != nil {
				if volume.EndTime.After(*result.EndTime) {
					*result.EndTime = *volume.EndTime
				}
			} else {
				result.EndTime = timeP(*volume.EndTime)
			}
		}

		if volume.StartTime != nil {
			if result.StartTime != nil {
				if volume.StartTime.Before(*result.StartTime) {
					*result.StartTime = *volume.StartTime
				}
			} else {
				result.StartTime = timeP(*volume.StartTime)
			}
		}

		if volume.SpatialVolume != nil {
			if result.SpatialVolume == nil {
				result.SpatialVolume = &Volume3D{}
			}

			if volume.SpatialVolume.AltitudeLo != nil {
				if result.SpatialVolume.AltitudeLo != nil {
					if *volume.SpatialVolume.AltitudeLo < *result.SpatialVolume.AltitudeLo {
						*result.SpatialVolume.AltitudeLo = *volume.SpatialVolume.AltitudeLo
					}
				} else {
					result.SpatialVolume.AltitudeLo = float32p(*volume.SpatialVolume.AltitudeLo)
				}
			}

			if volume.SpatialVolume.AltitudeHi != nil {
				if result.SpatialVolume.AltitudeHi != nil {
					if *volume.SpatialVolume.AltitudeHi > *result.SpatialVolume.AltitudeHi {
						*result.SpatialVolume.AltitudeHi = *volume.SpatialVolume.AltitudeHi
					}
				} else {
					result.SpatialVolume.AltitudeHi = float32p(*volume.SpatialVolume.AltitudeHi)
				}
			}

			if volume.SpatialVolume.Footprint != nil {
				cells, err := volume.SpatialVolume.Footprint.CalculateCovering()
				if err != nil {
					return nil, err
				}

				if result.SpatialVolume.Footprint == nil {
					result.SpatialVolume.Footprint = precomputedCellGeometry{}
				}
				result.SpatialVolume.Footprint.(precomputedCellGeometry).merge(cells...)
			}
		}
	}

	return result, nil
}

// CalculateSpatialCovering returns the spatial covering of vol4.
func (vol4 *Volume4D) CalculateSpatialCovering() (s2.CellUnion, error) {
	switch {
	case vol4.SpatialVolume == nil:
		return nil, ErrMissingSpatialVolume
	default:
		return vol4.SpatialVolume.CalculateCovering()
	}
}

// CalculateCovering returns the spatial covering of vol3.
func (vol3 *Volume3D) CalculateCovering() (s2.CellUnion, error) {
	switch {
	case vol3.Footprint == nil:
		return nil, ErrMissingFootprint
	default:
		return vol3.Footprint.CalculateCovering()
	}
}

// CalculateCovering returns the result of invoking gf.
func (gf GeometryFunc) CalculateCovering() (s2.CellUnion, error) {
	return gf()
}

// GeoCircle models a circular enclosed area on earth's surface.
type GeoCircle struct {
	Center      LatLngPoint
	RadiusMeter float32
}

// CalculateCovering returns the spatial covering of gc.
func (gc *GeoCircle) CalculateCovering() (s2.CellUnion, error) {
	if (gc.Center.Lat > maxLat) || (gc.Center.Lat < minLat) || (gc.Center.Lng > maxLng) || (gc.Center.Lng < minLng) {
		return nil, errBadCoordSet
	}

	if !(gc.RadiusMeter > 0) {
		return nil, errRadiusMustBeLargerThan0
	}

	return geo.CoveringForLoop(s2.RegularLoop(
		s2.PointFromLatLng(s2.LatLngFromDegrees(gc.Center.Lat, gc.Center.Lng)),
		geo.DistanceMetersToAngle(float64(gc.RadiusMeter)),
		20,
	))
}

// GeoPolygon models an enclosed area on the earth.
// The bounding edges of this polygon shall be the shortest paths between connected vertices.  This means, for instance, that the edge between two points both defined at a particular latitude is not generally contained at that latitude.
// The winding order shall be interpreted as the order which produces the smaller area.
// The path between two vertices shall be the shortest possible path between those vertices.
// Edges may not cross.
// Vertices may not be duplicated.  In particular, the final polygon vertex shall not be identical to the first vertex.
type GeoPolygon struct {
	Vertices []*LatLngPoint
}

// CalculateCovering returns the spatial covering of gp.
func (gp *GeoPolygon) CalculateCovering() (s2.CellUnion, error) {
	var points []s2.Point
	if gp == nil {
		return nil, errBadCoordSet
	}
	for _, v := range gp.Vertices {
		// ensure that coordinates passed are actually on earth
		if (v.Lat > maxLat) || (v.Lat < minLat) || (v.Lng > maxLng) || (v.Lng < minLng) {
			return nil, errBadCoordSet
		}
		points = append(points, s2.PointFromLatLng(s2.LatLngFromDegrees(v.Lat, v.Lng)))
	}
	if len(points) < 3 {
		return nil, errNotEnoughPointsInPolygon
	}
	return geo.Covering(points)
}

// LatLngPoint models a point on the earth's surface.
type LatLngPoint struct {
	Lat float64
	Lng float64
}

// Volume4DFromRIDProto convert proto to model object
func Volume4DFromRIDProto(vol4 *ridpb.Volume4D) (*Volume4D, error) {
	vol3, err := Volume3DFromRIDProto(vol4.GetSpatialVolume())
	if err != nil {
		return nil, err
	}

	result := &Volume4D{
		SpatialVolume: vol3,
	}

	if startTime := vol4.GetTimeStart(); startTime != nil {
		ts, err := ptypes.Timestamp(startTime)
		if err != nil {
			return nil, err
		}
		result.StartTime = &ts
	}

	if endTime := vol4.GetTimeEnd(); endTime != nil {
		ts, err := ptypes.Timestamp(endTime)
		if err != nil {
			return nil, err
		}
		result.EndTime = &ts
	}

	return result, nil
}

// Volume3DFromRIDProto convert proto to model object
func Volume3DFromRIDProto(vol3 *ridpb.Volume3D) (*Volume3D, error) {
	footprint := vol3.GetFootprint()
	if footprint == nil {
		return nil, errors.New("spatial_volume missing required footprint")
	}
	polygonFootprint := GeoPolygonFromRIDProto(footprint)

	result := &Volume3D{
		Footprint:  polygonFootprint,
		AltitudeLo: proto.Float32(vol3.GetAltitudeLo()),
		AltitudeHi: proto.Float32(vol3.GetAltitudeHi()),
	}

	return result, nil
}

// GeoPolygonFromRIDProto convert proto to model object
func GeoPolygonFromRIDProto(footprint *ridpb.GeoPolygon) *GeoPolygon {
	result := &GeoPolygon{}

	for _, ltlng := range footprint.Vertices {
		result.Vertices = append(result.Vertices, PointFromRIDProto(ltlng))
	}

	return result
}

// PointFromRIDProto convert proto to model object
func PointFromRIDProto(pt *ridpb.LatLngPoint) *LatLngPoint {
	return &LatLngPoint{
		Lat: pt.Lat,
		Lng: pt.Lng,
	}
}

// Business -> RID

// ToRIDProto converts Volume4D model obj to proto
func (vol4 *Volume4D) ToRIDProto() (*ridpb.Volume4D, error) {
	vol3, err := vol4.SpatialVolume.ToRIDProto()
	if err != nil {
		return nil, err
	}

	result := &ridpb.Volume4D{
		SpatialVolume: vol3,
	}

	if vol4.StartTime != nil {
		ts, err := ptypes.TimestampProto(*vol4.StartTime)
		if err != nil {
			return nil, err
		}
		result.TimeStart = ts
	}

	if vol4.EndTime != nil {
		ts, err := ptypes.TimestampProto(*vol4.EndTime)
		if err != nil {
			return nil, err
		}
		result.TimeEnd = ts
	}

	return result, nil
}

// ToRIDProto converts Volume3D model obj to proto
func (vol3 *Volume3D) ToRIDProto() (*ridpb.Volume3D, error) {
	if vol3 == nil {
		return nil, nil
	}

	result := &ridpb.Volume3D{}

	if vol3.AltitudeLo != nil {
		result.AltitudeLo = *vol3.AltitudeLo
	}

	if vol3.AltitudeHi != nil {
		result.AltitudeHi = *vol3.AltitudeHi
	}

	switch t := vol3.Footprint.(type) {
	case nil:
		// Empty on purpose
	case *GeoPolygon:
		result.Footprint = t.ToRIDProto()
	default:
		return nil, fmt.Errorf("unsupported geometry type: %T", vol3.Footprint)
	}

	return result, nil
}

// ToRIDProto converts GeoPolygon model obj to proto
func (gp *GeoPolygon) ToRIDProto() *ridpb.GeoPolygon {
	if gp == nil {
		return nil
	}

	result := &ridpb.GeoPolygon{}

	for _, pt := range gp.Vertices {
		result.Vertices = append(result.Vertices, pt.ToRIDProto())
	}

	return result
}

// ToRIDProto converts latlngpoint model obj to proto
func (pt *LatLngPoint) ToRIDProto() *ridpb.LatLngPoint {
	result := &ridpb.LatLngPoint{
		Lat: pt.Lat,
		Lng: pt.Lng,
	}

	return result
}

// Volume4DFromSCDProto converts vol4 proto to a Volume4D
func Volume4DFromSCDProto(vol4 *scdpb.Volume4D) (*Volume4D, error) {
	vol3, err := Volume3DFromSCDProto(vol4.GetVolume())
	if err != nil {
		return nil, err
	}

	result := &Volume4D{
		SpatialVolume: vol3,
	}

	if startTime := vol4.GetTimeStart(); startTime != nil {
		st := startTime.GetValue()
		ts, err := ptypes.Timestamp(st)
		if err != nil {
			return nil, err
		}
		result.StartTime = &ts
	}

	if endTime := vol4.GetTimeEnd(); endTime != nil {
		et := endTime.GetValue()
		ts, err := ptypes.Timestamp(et)
		if err != nil {
			return nil, err
		}
		result.EndTime = &ts
	}

	return result, nil
}

// Volume3DFromSCDProto converts a vol3 proto to a Volume3D
func Volume3DFromSCDProto(vol3 *scdpb.Volume3D) (*Volume3D, error) {
	switch {
	case vol3.GetOutlineCircle() != nil && vol3.GetOutlinePolygon() != nil:
		return nil, errors.New("both circle and polygon specified in outline geometry")
	case vol3.GetOutlinePolygon() != nil:
		return &Volume3D{
			Footprint:  GeoPolygonFromSCDProto(vol3.GetOutlinePolygon()),
			AltitudeLo: float32p(float32(vol3.GetAltitudeLower().GetValue())),
			AltitudeHi: float32p(float32(vol3.GetAltitudeUpper().GetValue())),
		}, nil
	case vol3.GetOutlineCircle() != nil:
		return &Volume3D{
			Footprint:  GeoCircleFromSCDProto(vol3.GetOutlineCircle()),
			AltitudeLo: float32p(float32(vol3.GetAltitudeLower().GetValue())),
			AltitudeHi: float32p(float32(vol3.GetAltitudeUpper().GetValue())),
		}, nil
	}

	return &Volume3D{
		AltitudeLo: float32p(float32(vol3.GetAltitudeLower().GetValue())),
		AltitudeHi: float32p(float32(vol3.GetAltitudeUpper().GetValue())),
	}, nil
}

// GeoCircleFromSCDProto converts a circle proto to a GeoCircle
func GeoCircleFromSCDProto(c *scdpb.Circle) *GeoCircle {
	return &GeoCircle{
		Center:      *LatLngPointFromSCDProto(c.GetCenter()),
		RadiusMeter: unitToMeterMultiplicativeFactors[unit(c.GetRadius().GetUnits())] * c.GetRadius().GetValue(),
	}
}

// GeoPolygonFromSCDProto converts a polygon proto to a GeoPolygon
func GeoPolygonFromSCDProto(p *scdpb.Polygon) *GeoPolygon {
	result := &GeoPolygon{}
	for _, ltlng := range p.GetVertices() {
		result.Vertices = append(result.Vertices, LatLngPointFromSCDProto(ltlng))
	}

	return result
}

// LatLngPointFromSCDProto converts a point proto to a latlngpoint
func LatLngPointFromSCDProto(p *scdpb.LatLngPoint) *LatLngPoint {
	return &LatLngPoint{
		Lat: p.GetLat(),
		Lng: p.GetLng(),
	}
}

// ToSCDProto converts the Volume4D to a proto
func (vol4 *Volume4D) ToSCDProto() (*scdpb.Volume4D, error) {
	vol3, err := vol4.SpatialVolume.ToSCDProto()
	if err != nil {
		return nil, err
	}

	result := &scdpb.Volume4D{
		Volume: vol3,
	}

	if vol4.StartTime != nil {
		ts, err := ptypes.TimestampProto(*vol4.StartTime)
		if err != nil {
			return nil, err
		}
		result.TimeStart = &scdpb.Time{
			Format: TimeFormatRFC3339,
			Value:  ts,
		}
	}

	if vol4.EndTime != nil {
		ts, err := ptypes.TimestampProto(*vol4.EndTime)
		if err != nil {
			return nil, err
		}
		result.TimeEnd = &scdpb.Time{
			Format: TimeFormatRFC3339,
			Value:  ts,
		}
	}

	return result, nil
}

// ToSCDProto converts the Volume3D to a proto
func (vol3 *Volume3D) ToSCDProto() (*scdpb.Volume3D, error) {
	if vol3 == nil {
		return nil, nil
	}

	result := &scdpb.Volume3D{}

	if vol3.AltitudeLo != nil {
		result.AltitudeLower = &scdpb.Altitude{
			Reference: altitudeReferenceWGS84.String(),
			Units:     unitMeter.String(),
			Value:     float64(*vol3.AltitudeLo),
		}
	}

	if vol3.AltitudeHi != nil {
		result.AltitudeUpper = &scdpb.Altitude{
			Reference: altitudeReferenceWGS84.String(),
			Units:     unitMeter.String(),
			Value:     float64(*vol3.AltitudeHi),
		}
	}

	switch t := vol3.Footprint.(type) {
	case nil:
		// Empty on purpose
	case *GeoPolygon:
		result.OutlinePolygon = t.ToSCDProto()
	case *GeoCircle:
		result.OutlineCircle = t.ToSCDProto()
	}

	return result, nil
}

// ToSCDProto converts the GeoCircle to a proto
func (gc *GeoCircle) ToSCDProto() *scdpb.Circle {
	if gc == nil {
		return nil
	}

	return &scdpb.Circle{
		Center: gc.Center.ToSCDProto(),
		Radius: &scdpb.Radius{
			Units: unitMeter.String(),
			Value: gc.RadiusMeter,
		},
	}
}

// ToSCDProto converts the GeoPolygon to a proto
func (gp *GeoPolygon) ToSCDProto() *scdpb.Polygon {
	if gp == nil {
		return nil
	}

	result := &scdpb.Polygon{}

	for _, pt := range gp.Vertices {
		result.Vertices = append(result.Vertices, pt.ToSCDProto())
	}

	return result
}

// ToSCDProto converts the LatLngPoint to a proto
func (pt *LatLngPoint) ToSCDProto() *scdpb.LatLngPoint {
	result := &scdpb.LatLngPoint{
		Lat: pt.Lat,
		Lng: pt.Lng,
	}

	return result
}
