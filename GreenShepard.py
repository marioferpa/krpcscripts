#C:\Users\Mario>C:\Python27\python.exe C:\Users\Mario\Dropbox\Python\Kerbal\GreenShepard.py


import krpc, time
from math import log

conn = krpc.connect(name='Green Shepard')
vessel = conn.space_center.active_vessel

print("VESSEL INFO")
print("")
print "Vessel name: ", vessel.name
print ("")

#if vessel.name != "Green Shepard":



print("PRE FLIGHT CHECK")
print("")

if vessel.comms.has_connection:
    print "The ship has a flight computer"
else:
    print "The ship doesn't have a flight computer"


vessel.control.sas = False
vessel.control.rcs = False
print "SAS and RCS off."


for landing_leg in vessel.parts.landing_legs:
    landing_leg.deployed = False
print "Landing legs retracted."

supersonic = False

print ("")
print "Program sequence: launch.exe -> first_stage.exe ->"
print "second_stage.exe -> coasting.exe ->"
print "suicide_burn_vertical.exe -> exit.exe"
print ("")




## REFERENCE FRAMES

KCKF = vessel.orbit.body.reference_frame
# Kerbin-Centered, Kerbin-Fixed reference frame.
# Although this actually works for whatever body
# the ship is orbiting.


## STREAMS

ut = conn.add_stream(getattr, conn.space_center, 'ut')

stage0resources = vessel.resources_in_decouple_stage(stage=0, cumulative=False)
stage0fuel = conn.add_stream(stage0resources.amount, "LiquidFuel")
stage2resources = vessel.resources_in_decouple_stage(stage=2, cumulative=False)
stage2fuel = conn.add_stream(stage2resources.amount, "LiquidFuel")
stage3resources = vessel.resources_in_decouple_stage(stage=3, cumulative=False)
stage3fuel = conn.add_stream(stage3resources.amount, "LiquidFuel")

speed = conn.add_stream(getattr, vessel.flight(KCKF), "speed")
v_speed = conn.add_stream(getattr, vessel.flight(KCKF), "vertical_speed")

altitude = conn.add_stream(getattr, vessel.flight(KCKF), "mean_altitude")
surface_altitude = conn.add_stream(getattr, vessel.flight(KCKF), "surface_altitude")
apo_altitude = conn.add_stream(getattr, vessel.orbit, "apoapsis_altitude")



## FUNCTIONS

def twr():
    thrust = vessel.thrust
    weight = vessel.mass * vessel.orbit.body.surface_gravity
    return thrust / weight


go = raw_input("Request launch (y/n) or a specific program: ")
#go = "Y"


if go.lower() == "y":
    print "Initiating launch sequence"
    time.sleep(3)
    program = "launch.exe"

elif go.lower() == "n":
    print "No go"
    program = "exit.exe"

else:
    program = go



while program != "exit.exe":

    ###################################################

    if program == "launch.exe":    #launch sequence

        vessel.auto_pilot.engage()
        vessel.auto_pilot.target_pitch_and_heading(90,90)
        vessel.control.throttle = 1

        print "3..."
        time.sleep(1)
        print "2..."
        time.sleep(1)
        print "1..."
        time.sleep(1)
        print "Liftoff!"
        vessel.control.activate_next_stage()    #all engines start

        while speed() <= 50:
            pass

        program = "first_stage.exe"

    ###################################################

    if program == "first_stage.exe":

        print "First stage."

        while stage3fuel() >= 1:
            pass

        print "Staging boosters."
        vessel.control.activate_next_stage()    #booster ejection

        program = "second_stage.exe"

    ###################################################

    if program == "second_stage.exe":

        print "Second stage"

        while apo_altitude() <= 80000:
            pass

        print "Boost complete, throttle killed."
        vessel.control.throttle = 0
        time.sleep(1)
        vessel.control.activate_next_stage()    #booster ejection
        time.sleep(1)
        vessel.control.activate_next_stage()    #landing engines activated

        program = "coasting.exe"

    ###################################################

    if program == "coasting.exe":

        print "Waiting for apoapse"

        while v_speed() > 0:
            pass

        print "Maximum altitude reached.",

        program = "suicide_burn_vertical.exe"

    ###################################################

    if program == "suicide_burn_vertical.exe":

        print "Pointing retrograde"
        vessel.auto_pilot.engage()
        vessel.control.sas = True
        time.sleep(1)
        #vessel.control.sas_mode = conn.space_center.SASMode.retrograde
        vessel.auto_pilot.target_pitch_and_heading(90,90)

        #Max thrust. This kills the kerbal.

        while altitude() >= 23000:
            pass

        print "This is fine."


        active_engines = filter(lambda e: e.active and e.has_fuel, vessel.parts.engines)
        max_thrust = sum(engine.available_thrust for engine in active_engines)
        isp = max_thrust / sum(engine.available_thrust / engine.kerbin_sea_level_specific_impulse for engine in active_engines) #aprox. constant
        g = vessel.orbit.body.surface_gravity
        delta_t = 0.1 #time step for the integration

        while True:

            critical_altitude = 0
            m_i = vessel.mass
            v = speed()

            while v >= 0:

                a_b = (max_thrust / m_i) - g
                m_f = m_i - (max_thrust * delta_t)/(g * isp)
                delta_v = g * isp * log(m_i / m_f)
                delta_h = v * (delta_v / a_b) - ((delta_v ** 2)/(2 * a_b))

                critical_altitude += delta_h
                v -= delta_v
                m_i = m_f

#            print "Crit h = %s, m_f = %s, delta_v = %s, delta_h = %s" % (critical_altitude, m_f, delta_v, delta_h)


            if surface_altitude() <= critical_altitude:
                print "Critical altitude reached: %s" % surface_altitude()
                break

        print "Burn!!"

        while abs(v_speed()) >= 30.0:
            vessel.control.throttle = 1

        for landing_leg in vessel.parts.landing_legs:
            landing_leg.deployed = True

        print "Landing legs deployed."

        vessel.control.throttle = 0.1

        landing_v = -10.0

        kp = 0.2
        ki = 0.00002
        kd = 0.45

        reset = 0
        lasterror = 0

        # PID loop
        while str(vessel.situation) != "VesselSituation.landed":

            error = landing_v - v_speed()
            reset = reset + error

            pid = kp * error + ki * reset + kd * (error - lasterror) #o al reves?

            lasterror = error

#            print "Error = %s, reset = %s, pid = %s" % (error, reset, pid)


            if pid + vessel.control.throttle > 1:
                vessel.control.throttle = 1
            elif pid + vessel.control.throttle < 0:
                vessel.control.throttle = 0
            else:
                vessel.control.throttle = pid

        vessel.control.throttle = 0
        print "PHEW"

        program = "exit.exe"
