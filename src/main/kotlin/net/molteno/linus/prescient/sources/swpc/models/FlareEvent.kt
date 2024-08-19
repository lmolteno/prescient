package net.molteno.linus.prescient.sources.swpc.models

import kotlinx.datetime.Instant

data class FlareEvent(
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

    val location: String,
    /**
     * Importance is the corrected area of the flare in heliospheric square degrees at maximum
     * brightness, observed in the H-alpha line (656.3 nm).
     * 	       S - Subflare (area < or =2.0 square degrees).
     *
     * 	       1 - Importance 1  ( 2.1 <= area <=  5.1 square degrees)
     *
     *     	   2 - Importance 2  ( 5.2 <= area <= 12.4 square degrees)
     *
     * 	       3 - Importance 3  (12.5 <= area <= 24.7 square degrees)
     *
     * 	       4 - Importance 4  (area >= 24.8 square degrees)
     */
    val importance: Char,
    /**
     * 	    Brightness is the relative maximum brightness of flare in H-alpha.
     *  	       F - faint	N - normal	B - brilliant
     */
    val brightness: FlareBrightness,
    val characteristics: List<FlareCharacteristic>
): SolarEventObservation {
    enum class FlareBrightness { F, N, B }
    enum class FlareCharacteristic {
        VWL, // visible in white light
        UMB, // greater than or equal to 20% umbral coverage
        PRB, // Parallel ribbon
        LPS, // Associated Loop Prominence (LPS)
        YSR, // Y-shaped ribbon
        ERU, // Several eruptive centers
        BPT, // One or more brilliant points
        HSS, // Associated high speed dark or bright surge
        DSD, // Dark surge on the disk
        DSF, // Flare followed the disappearance of a solar filament in the same region
        BLU, // H-alpha emission greater in the blue wing than in the red wing
    }
}