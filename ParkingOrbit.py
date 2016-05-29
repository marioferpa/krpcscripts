import krpc, time, math

conn = krpc.connect(name='Parking Orbit')
vessel = conn.space_center.active_vessel

print("VESSEL INFO")
print("")
print "Vessel name: ", vessel.name
print vessel.type
print vessel.situation
print ("")


print("PRE FLIGHT CHECK")
print("")

if vessel.comms.has_connection:
    print "The ship has a flight computer"
else:
    print "The ship doesn't have a flight computer"


vessel.control.sas = False
print "SAS disengaged"
vessel.control.rcs = False
print "RCS disengaged"

print ("")





## Reference frames

KCKF = vessel.orbit.body.reference_frame
# Kerbin-Centered, Kerbin-Fixed reference frame.
# Although this actually works for whatever body
# the ship is orbiting.


## Streams

ut = conn.add_stream(getattr, conn.space_center, 'ut')

stage1resources = vessel.resources_in_decouple_stage(stage=1, cumulative=False)
stage1fuel = conn.add_stream(stage1resources.amount, "LiquidFuel")
stage2resources = vessel.resources_in_decouple_stage(stage=0, cumulative=False)
stage2fuel = conn.add_stream(stage2resources.amount, "LiquidFuel")

speed = conn.add_stream(getattr, vessel.flight(KCKF), "speed")

altitude = conn.add_stream(getattr, vessel.flight(KCKF), "mean_altitude")
apo_altitude = conn.add_stream(getattr, vessel.orbit, "apoapsis_altitude")


def twr():
    thrust = vessel.thrust
    weight = vessel.mass * vessel.orbit.body.surface_gravity
    return thrust / weight




#target = raw_input("Enter the desired target altitude in km: ")
#fuel check
go = raw_input("Proceed to launch? (y/n)")

target = 80

supersonic = False

if go.lower() != "y":
    print "No go, I repeat, no go"
    program = "exit.exe"

else:
    program = "launch.exe"


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
        vessel.control.activate_next_stage()    #main engine ignition
        print "1..."
        time.sleep(1)
        print "aaaand LIFTOFFFFF"
        vessel.control.activate_next_stage()    #launch clamps release

        while speed() <= 50:
            pass


        program = "pitchover_maneuver.exe"


    ###################################################


    if program == "pitchover_maneuver.exe":

        print "Pitchover maneuver"

        vessel.auto_pilot.target_pitch_and_heading(80,90)  #pending: asking for target inclination
        time.sleep(3)
        vessel.auto_pilot.disengage()

        print "Auto pilot disengaged"

        program = "first_stage.exe"


    ###################################################


    if program == "first_stage.exe":


        vessel.control.throttle = 0.9

        while stage1fuel() > 0.1:
            if speed() >= 340 and supersonic == False: #it won't be 340 at that altitude
                print "The rocket is now supersonic"
                supersonic = True
            #else:
             #   pass

        program = "second_stage.exe"


    ###################################################


    if program == "second_stage.exe":

        print "SAS engaged"
        vessel.control.sas = True
        time.sleep(1)
        vessel.control.sas_mode = conn.space_center.SASMode.prograde
        vessel.control.throttle = 0
        print "Main engine cutoff"
        vessel.control.activate_next_stage() #MECO
        print "Secondary engine activated"
        vessel.control.throttle = 0.2

        while apo_altitude() <= target * 1000:
            pass

        vessel.control.throttle = 0
        program = "burn_circularization_calculation.exe"
        print "Coasting to apoapse"

    ###################################################

    # As this program is currently written it must be run once the ship is
    # outside the atmosphere or the calculation will be slightly wrong.

    if program == "burn_circularization_calculation.exe":

        print "Calculating circularization maneuver"

        mu = vessel.orbit.body.gravitational_parameter
        r = vessel.orbit.apoapsis
        a1 = vessel.orbit.semi_major_axis
        a2 = r

        v1 = math.sqrt(mu*((2./r)-(1./a1)))
        v2 = math.sqrt(mu*((2./r)-(1./a2)))
        delta_v = v2 - v1

        node = vessel.control.add_node(ut()+vessel.orbit.time_to_apoapsis, prograde=delta_v)

        #check if there's enough fuel
        #if not, inform of the predicted resulting periapse

        program = "exit.exe"
