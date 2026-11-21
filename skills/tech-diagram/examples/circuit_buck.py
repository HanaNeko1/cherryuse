"""BUCK converter schematic — schemdraw template.

Usage:  python circuit_buck.py [output.png]
"""

import sys

import schemdraw
import schemdraw.elements as elm

schemdraw.use("matplotlib")  # REQUIRED for PNG output

out = sys.argv[1] if len(sys.argv) > 1 else "buck_basic.png"

# Layout coordinates (inches). Keep >= 1 inch between parallel vertical elements.
Y_TOP, Y_BOT = 3, 0
X_VIN, X_CIN, X_SW_IN, X_SW, X_OUT, X_RL = 0, 1.3, 2.3, 4.0, 6.5, 8.1

with schemdraw.Drawing(file=out, show=False) as d:
    d.config(fontsize=12, unit=3)

    # Input source
    d += elm.SourceV().at((X_VIN, Y_BOT)).up().length(Y_TOP)

    # Top rail: Vin -> Cin tap -> switch
    d += elm.Line().at((X_VIN, Y_TOP)).right().length(X_SW_IN - X_VIN)
    d += elm.Dot().at((X_CIN, Y_TOP))

    # Input capacitor
    d += elm.Capacitor().at((X_CIN, Y_TOP)).down().length(Y_TOP)
    d += elm.Dot().at((X_CIN, Y_BOT))

    # High-side switch
    d += elm.Switch().at((X_SW_IN, Y_TOP)).right().length(X_SW - X_SW_IN)

    # SW node
    d += elm.Dot().at((X_SW, Y_TOP))

    # Freewheeling diode: cathode at SW, anode to ground
    d += elm.Diode().at((X_SW, Y_TOP)).down().length(Y_TOP).reverse()
    d += elm.Dot().at((X_SW, Y_BOT))

    # Inductor
    d += elm.Inductor().at((X_SW, Y_TOP)).right().length(X_OUT - X_SW)

    # Output node
    d += elm.Dot().at((X_OUT, Y_TOP))

    # Output capacitor
    d += elm.Capacitor().at((X_OUT, Y_TOP)).down().length(Y_TOP)
    d += elm.Dot().at((X_OUT, Y_BOT))

    # Load
    d += elm.Line().at((X_OUT, Y_TOP)).right().length(X_RL - X_OUT)
    d += elm.Resistor().at((X_RL, Y_TOP)).down().length(Y_TOP)

    # Bottom rail and ground
    d += elm.Line().at((X_VIN, Y_BOT)).right().length(X_RL - X_VIN)
    d += elm.Ground().at((X_VIN, Y_BOT))

    # Labels (absolute positions keep them clear of symbols)
    d += elm.Label().at((X_VIN - 0.95, 1.5)).label("V_in")
    d += elm.Label().at((X_CIN + 0.85, 1.5)).label("C_in")
    d += elm.Label().at((X_SW_IN + 0.55, Y_TOP - 0.4)).label("S")
    d += elm.Label().at((X_SW - 0.75, 1.5)).label("D")
    d += elm.Label().at((X_SW + 0.9, Y_TOP + 0.45)).label("L")
    d += elm.Label().at((X_OUT + 0.6, Y_TOP - 0.4)).label("V_o")
    d += elm.Label().at((X_OUT + 0.8, 1.5)).label("C_o")
    d += elm.Label().at((X_RL + 0.55, 1.5)).label("R_L")

print("OK:", out)
