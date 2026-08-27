// Agent Body Protocol — lamp BASE exploded drawing.
// Phase 1–3 path only. Not a manufactured part. Not a pack we shipped.
// Rage Industries built the protocol, not the lamp.
//
//   openscad docs/hardware/base-exploded.scad
//
// Occupancy (bottom → top), all in the BASE, never the shade/head:
//   1. Qi RX coil (Phase 3 drawing — not shipped)
//   2. 18650/21700 + BMS (Phase 2 drawing — not shipped; BMS required)
//   3. Phase 1 divider + ADS1115 on the 12 V wall rail (this PR: software + drawing)
//   4. USB-C charge jack on the base rim (Phase 2 drawing)
// Thermal: pack/BMS sit in the base, away from the LED head.

$fn = 48;
gap = 18;

module base_shell() {
    color([0.15, 0.15, 0.18])
        difference() {
            cylinder(h = 22, d = 90);
            translate([0, 0, 3]) cylinder(h = 20, d = 80);
        }
}

module qi_rx_coil() {
    // Phase 3 drawing. Coil under the base, facing the bench TX pad.
    color([0.85, 0.65, 0.15])
        difference() {
            cylinder(h = 2, d = 40);
            translate([0, 0, -0.5]) cylinder(h = 3, d = 16);
        }
}

module pack_and_bms() {
    // Phase 2 drawing. 3S 18650/21700 + BMS. No homemade pouch.
    for (i = [-1, 0, 1]) {
        translate([i * 20, 0, 0])
            color([0.2, 0.2, 0.25]) cylinder(h = 65, d = 18);
    }
    translate([-28, 16, 10])
        color([0.1, 0.45, 0.2]) cube([56, 4, 16], center = false);
}

module divider_adc() {
    // Phase 1: 39.2 kΩ / 10.0 kΩ into ADS1115 (Adafruit 1085). 12 V rail tap.
    color([0.12, 0.35, 0.55]) cube([26, 18, 5], center = true);
    translate([16, 0, 0]) color([0.7, 0.15, 0.15]) cube([4, 10, 3], center = true); // R_high
    translate([21, 0, 0]) color([0.15, 0.15, 0.7]) cube([4, 10, 3], center = true); // R_low
}

module usbc_jack() {
    color([0.4, 0.4, 0.42]) cube([9, 7, 3], center = true);
}

module led_head_ghost() {
    // Not a power location. Shown only so the drawing keeps the head empty.
    color([0.8, 0.8, 0.85, 0.15])
        translate([0, 0, 0]) cylinder(h = 30, d = 50);
}

translate([0, 0, 0]) qi_rx_coil();
translate([0, 0, gap]) pack_and_bms();
translate([0, 0, gap * 2 + 40]) divider_adc();
translate([40, 0, gap * 2 + 40]) usbc_jack();
translate([0, 0, gap * 3 + 50]) base_shell();
translate([0, 0, gap * 4 + 70]) led_head_ghost();
