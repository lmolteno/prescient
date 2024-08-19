package net.molteno.linus.prescient.sources.swpc.models

import kotlinx.datetime.Instant

data class SweptRadioBurstEvent(
    override val region: Int?,
    override val eventId: Int,

    override val beginDatetime: Instant,
    override val beginQuality: String?,

    override val maxDatetime: Instant?,
    override val maxQuality: String?,

    override val endDatetime: Instant?,
    override val endQuality: String?,

    override val type: SolarEventType,
    override val observatory: SolarObservatory,
    override val quality: String,

    override val statusCode: Int,
    override val statusText: String,
    override val changeFlag: Int,

    val frequencyRange: IntRange,

    val radioBurstType: RadioBurstType,
    /** Intensity is a relative scale 1=Minor, 2=Significant, 3=Major */
    val intensity: Int
): SolarEventObservation {
    enum class RadioBurstType {
        /** Slow drift burst */
        II,
        /** Fast drift burst */
        III,
        /** Broadband smooth continuum burst */
        IV,
        /** Brief continuum burst, generally associated with Type III bursts */
        V,
        /** Series of Type III bursts over a period of 10 minutes or more,with no period longer than 30 minutes without activity */
        VI,
        /** Series of Type III and Type V bursts over a period of 10 minutesor more, with no period longer than 30 minutes without activity */
        VII,
        /** Broadband, long-lived, dekametric continuum */
        CTM
    }
}
