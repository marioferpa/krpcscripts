import krpc, time

conn = krpc.connect(name='Parking Orbit')
vessel = conn.space_center.active_vessel

print("VESSEL INFO")
print("")
print "Vessel name: ", vessel.name
print vessel.type
print vessel.situation
print "Terminal velocity: ", vessel.flight().terminal_velocity
stage1resources = vessel.resources_in_decouple_stage(stage=1, cumulative=False)
print "Liquid fuel in 1st stage: ", stage1resources.amount("LiquidFuel")
print ("")


print("PRE FLIGHT CHECK")
print("")

if vessel.comms.has_connection:
    state = "has"
else:
    state = "doesn't have"
    
print("The ship %s a flight computer" % state)
print ("")
print "Add a known state here (SAS, solar panels...)"
print ""


vessel.control.sas = False


## Reference frames

KCKF = vessel.orbit.body.reference_frame
# Kerbin-Centered, Kerbin-Fixed reference frame.
#Although this actually works for whatever body
# the ship is orbiting.


## Streams
    
stage1fuel = conn.add_stream(stage1resources.amount, "LiquidFuel")

speed = conn.add_stream(getattr, vessel.flight(KCKF), "speed")
altitude = conn.add_stream(getattr, vessel.flight(KCKF), "mean_altitude")


#termvel = conn.add_stream(getattr, vessel.flight(), "terminal_velocity")
    #por si hace falta alguna vez, se hace print termvel()

#target = raw_input("Enter the desired target altitude: ")
#fuel check
#go = raw_input("Proceed to launch? (y/n)")

target = 100
go = "Y"

if go.lower() != "y":
    print "No go, I repeat, no go"
    program = "Exit"

else:
    program = "launch.exe"


while program != "exit.exe":

    ###################################################


    if program == "launch.exe":    #launch sequence
        
        vessel.auto_pilot.target_pitch_and_heading(90,90)
        vessel.auto_pilot.engage()
        vessel.control.throttle = 1

        print "3"
        time.sleep(1)
        print "2"
        time.sleep(1)
        vessel.control.activate_next_stage()    #main engine ignition
        print "1"
        time.sleep(1)
        print "LAUNCH"
        vessel.control.activate_next_stage()    #launch clamps release

        while speed() <= 50:
            pass

        

        program = "first_stage.exe"

    ###################################################

    if program == "pitchover_maneuver.exe":
        
        vessel.auto_pilot.target_pitch_and_heading(80,90)  #pending: asking for target inclination
        time.sleep(5)                                      
        vessel.auto_pilot.disengage()                       
        
    ###################################################

            
    if program == "first_stage.exe":    #first stage
        
        print program
        
        vessel.control.throttle = 0.9
            
        while stage1fuel() > 0.1:
            #print vessel.direction(KCKF)
            pass

        program = "second_stage.exe"
        

    ###################################################

 
    if program == "second_stage.exe":

        print program

        vessel.control.sas = True
        time.sleep(1)
        vessel.control.sas_mode = conn.space_center.SASMode.prograde
        vessel.control.throttle = 0
        vessel.control.activate_next_stage()
        vessel.control.throttle = 0.3
            
        while True:
            pass


    ###################################################
