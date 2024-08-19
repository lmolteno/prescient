package net.molteno.linus.prescient.sources.swpc.models

import kotlinx.datetime.Instant
import kotlinx.datetime.LocalDate
import kotlinx.serialization.Serializable

@Serializable
data class SolarRegionObservationDto (
    val region: Int,
    val latitude: Int?,
    val longitude: Int?,
    val location: String?,
    val observedDate: String, // iso 8601
    val carringtonLongitude: Int,
    val area: Int?,
    val spotClass: String?,
    val extent: Int?,
    val numberSpots: Int?,
    val magClass: String?,
    val magString: String?,
    val status: String?,
    val cXrayEvents: Int,
    val mXrayEvents: Int,
    val xXrayEvents: Int,
    val protonEvents: Int?,
    val cFlareProbability: Int,
    val mFlareProbability: Int,
    val xFlareProbability: Int,
    val protonProbability: Int?,
    val firstDate: String // iso 8601
)

data class SolarRegionObservation (
    val region: Int,
    val latitude: Int,
    val longitude: Int,
    val location: String,
    val observedDate: LocalDate, // iso 8601
    val carringtonLongitude: Int,
    val area: Int,
    val spotClass: String?,
    val extent: Int,
    val numberSpots: Int,
    val magClass: String?,
    val magString: String?,
    val status: String?,
    val cXrayEvents: Int,
    val mXrayEvents: Int,
    val xXrayEvents: Int,
    val protonEvents: Int?,
    val cFlareProbability: Int,
    val mFlareProbability: Int,
    val xFlareProbability: Int,
    val protonProbability: Int?,
    val firstDate: Instant // iso 8601
)

fun SolarRegionObservationDto.toSolarRegionObservation(): SolarRegionObservation? {
    if (latitude == null || longitude == null || location == null) return null

    return SolarRegionObservation(
        region = region,
        latitude = latitude,
        longitude = longitude,
        location = location,
        observedDate = LocalDate.parse(observedDate),
        carringtonLongitude = carringtonLongitude,
        area = area ?: return null,
        spotClass = spotClass,
        extent = extent ?: return null,
        numberSpots = numberSpots ?: return null,
        magClass = magClass,
        magString = magString,
        status = status,
        cXrayEvents = cXrayEvents,
        mXrayEvents = mXrayEvents,
        xXrayEvents = xXrayEvents,
        protonEvents = protonEvents,
        cFlareProbability = cFlareProbability,
        mFlareProbability = mFlareProbability,
        xFlareProbability = xFlareProbability,
        protonProbability = protonProbability,
        firstDate = Instant.parse(firstDate + "Z")
    )
}

/*
{
    "observed_date": "2024-05-13",
    "region": 3664,
    "latitude": -19,
    "longitude": -87,
    "location": "S19W87",
    "carrington_longitude": 348,
    "old_carrington_longitude": 349,
    "area": 1170,
    "spot_class": "Fkc",
    "extent": 24,
    "number_spots": 15,
    "mag_class": "BGD",
    "mag_string": null,
    "status": "f",
    "c_xray_events": 0,
    "m_xray_events": 5,
    "x_xray_events": 0,
    "proton_events": null,
    "s_flares": 6,
    "impulse_flares_1": 0,
    "impulse_flares_2": 0,
    "impulse_flares_3": 0,
    "impulse_flares_4": 0,
    "protons": 0,
    "c_flare_probability": 99,
    "m_flare_probability": 75,
    "x_flare_probability": 40,
    "proton_probability": 99,
    "first_date": "2024-05-01T16:42:56"
  },
 */
