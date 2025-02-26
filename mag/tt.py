import os
import gdsfactory as gf

# Parameters (adjust as needed)
TOP_LEVEL_CELL = "tt_rc_filter"
POWER_STRIPE_WIDTH = 2.0  # in microns
# Power stripe definitions: net name and x position in microns
POWER_STRIPES = {
    "VDPWR": 1.0,
    "VGND": 4.0,
    # Uncomment and add additional nets if needed, e.g.:
    # "VAPWR": 7.0,
}

# Layer definitions (example: met4 and a text layer; adjust as required)
LAYER_MET4 = (65, 20)
LAYER_TEXT = (66, 0)

# Create the top-level component
c = gf.Component(TOP_LEVEL_CELL)

# Define the vertical stripe vertical limits (in microns)
y_min = 5.0
y_max = 220.76
height = y_max - y_min


def draw_power_stripe(component, name, x):
    """Draw a vertical power stripe and add a port and label."""
    # Draw the stripe as a rectangle at position (x, y_min)
    # The rectangle spans from y_min to y_max with width POWER_STRIPE_WIDTH.
    points = [
        (x, y_min),
        (x + POWER_STRIPE_WIDTH, y_min),
        (x + POWER_STRIPE_WIDTH, y_max),
        (x, y_max),
    ]
    component.add_polygon(points, layer=LAYER_MET4)

    # Add a text label near the center of the stripe
    label_x = x + POWER_STRIPE_WIDTH / 2
    label_y = y_min + height / 2
    component.add_label(text=name, position=(label_x, label_y), layer=LAYER_TEXT)

    # Add a port at the center of the stripe
    # In this example the port is defined with the stripe width and placed at the center.
    # Set a property to indicate port use (mimicking Magic’s "port use")
    # port.properties["use"] = "ground" if name == "VGND" else "power"
    component.add_port(
        name=name,
        center=(label_x, label_y),
        width=POWER_STRIPE_WIDTH,
        orientation=0,  # 0° orientation (east); adjust if needed
        layer=LAYER_MET4,
        )


# Draw each power stripe defined in POWER_STRIPES
for net_name, x_position in POWER_STRIPES.items():
    print(f"Drawing power stripe {net_name} at {x_position} µm")
    draw_power_stripe(c, net_name, x_position)

# Create output directories if they don't exist
os.makedirs("gds", exist_ok=True)
os.makedirs("lef", exist_ok=True)

# Export the layout as GDS
gds_filename = f"gds/{TOP_LEVEL_CELL}.gds"
c.show()
c.write_gds(gds_filename)
print(f"GDS saved to {gds_filename}")

