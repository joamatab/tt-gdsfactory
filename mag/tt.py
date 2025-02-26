import os
import re
import gdsfactory as gf

# Parameters (adjust as needed)
TOP_LEVEL_CELL = "tt_um_rc_filter"
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


def def_orientation_to_angle(orient):
    """Convert DEF orientation (e.g. 'N') to an angle in degrees for gdsfactory.
    Here, 0° means east; so 'N' becomes 90°."""
    mapping = {"N": 90, "S": 270, "E": 0, "W": 180}
    return mapping.get(orient, 0)

def read_def_ports(def_file_path):
    """Read a DEF file and extract port definitions for met4.
    
    Each port in the DEF file has a block like:
    
        - <name> + NET <net> + DIRECTION <direction> + USE <use>
          + PORT
            + LAYER met4 ( <x1> <y1> ) ( <x2> <y2> )
            + PLACED ( <px> <py> ) <orient> ;
    
    Returns a list of port dictionaries.
    """
    with open(def_file_path, "r") as f:
        def_data = f.read()

    # Regular expression to capture the port data.
    pattern = re.compile(
        r"-\s+(?P<name>\S+)\s+\+ NET\s+(?P<net>\S+)\s+\+ DIRECTION\s+(?P<direction>\S+)\s+\+ USE\s+(?P<use>\S+).*?"
        r"\+ LAYER\s+met4\s+\(\s*(?P<x1>[-\d]+)\s+(?P<y1>[-\d]+)\s*\)\s+\(\s*(?P<x2>[-\d]+)\s+(?P<y2>[-\d]+)\s*\).*?"
        r"\+ PLACED\s+\(\s*(?P<px>[-\d]+)\s+(?P<py>[-\d]+)\s*\)\s+(?P<orient>\S+)\s*;",
        re.DOTALL
    )
    
    ports = []
    for match in pattern.finditer(def_data):
        name = match.group("name")
        net = match.group("net")
        direction = match.group("direction")
        use = match.group("use")
        # Get the bounding box coordinates (relative to port center)
        x1 = float(match.group("x1"))
        y1 = float(match.group("y1"))
        x2 = float(match.group("x2"))
        y2 = float(match.group("y2"))
        # Port placement
        px = float(match.group("px"))
        py = float(match.group("py"))
        orient = match.group("orient")
        
        # The DEF port box is defined from (x1, y1) to (x2, y2). Its width is:
        width = abs(x2 - x1)
        # And its height is:
        height = abs(y2 - y1)
        # Convert DEF orientation (e.g., 'N') to an angle (gdsfactory uses degrees)
        angle = def_orientation_to_angle(orient)
        
        ports.append({
            "name": name,
            "net": net,
            "direction": direction,
            "use": use,
            "center": (px, py),
            "width": width,
            "height": height,
            "orientation": angle
        })
    return ports

# For this example, we map DEF’s met4 layer to gdsfactory layer (65,20).
LAYER_MET4 = (65, 20)

# Read the DEF file.
def_file_path = "tt_analog_1x2_3v3.def"
ports = read_def_ports(def_file_path)

# Add each extracted port to the component.
for p in ports:
    # Create a port. In gdsfactory, the "width" is defined perpendicular to the port orientation.
    # Here we simply use the extracted width; you may wish to adjust if needed.
    port_center = p["center"]
    center = (port_center[0]*1e-3, port_center[1]*1e-3)
    width = p["width"] * 1e-3
    height = p["height"] * 1e-3
    c.add_port(
        name=p["name"],
        center=center,
        width=width,
        orientation=p["orientation"],
        layer=LAYER_MET4,
        port_type="electrical"
    )
    # Optionally, add a polygon to visualize the port.
    cx, cy = center
    dx = width / 2
    dy = height / 2
    poly_points = [
        (cx - dx, cy - dy),
        (cx + dx, cy - dy),
        (cx + dx, cy + dy),
        (cx - dx, cy + dy)
    ]
    c.add_polygon(poly_points, layer=LAYER_MET4)


# Export the layout as GDS
gds_filename = f"gds/{TOP_LEVEL_CELL}.gds"
c.show()
c.write_gds(gds_filename)
print(f"GDS saved to {gds_filename}")



