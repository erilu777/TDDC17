import java.text.DecimalFormat;
import java.text.NumberFormat;
import java.util.Locale;

public class TutorialController extends Controller {

    public SpringObject object;

    ComposedSpringObject cso;

    /* These are the agents senses (inputs) */
	DoubleFeature x; /* Positions */
	DoubleFeature y;
	DoubleFeature vx; /* Velocities */
	DoubleFeature vy;
	DoubleFeature angle; /* Angle */

    /* Example:
     * x.getValue() returns the vertical position of the rocket 
     */

	/* These are the agents actuators (outputs)*/
	RocketEngine leftRocket;
	RocketEngine middleRocket;
	RocketEngine rightRocket;

    /* Example:
     * leftRocket.setBursting(true) turns on the left rocket 
     */
	
	DecimalFormat df = (DecimalFormat) NumberFormat.getNumberInstance(Locale.US); 
	
	int iteration = 0;
	
	boolean hasBursted = false;
	
	public void init() {
		cso = (ComposedSpringObject) object;
		x = (DoubleFeature) cso.getObjectById("x");
		y = (DoubleFeature) cso.getObjectById("y");
		vx = (DoubleFeature) cso.getObjectById("vx");
		vy = (DoubleFeature) cso.getObjectById("vy");
		angle = (DoubleFeature) cso.getObjectById("angle");

		leftRocket = (RocketEngine) cso.getObjectById("rocket_engine_left");
		rightRocket = (RocketEngine) cso.getObjectById("rocket_engine_right");
		middleRocket = (RocketEngine) cso.getObjectById("rocket_engine_middle");

	}

    public void tick(int currentTime) {

    	/* TODO: Insert your code here */

    	iteration++;
    	
		System.out.println("ITERATION: " + iteration + " SENSORS: angle=" + df.format(angle.getValue()) + " vx=" + df.format(vx.getValue()) + " vy=" + df.format(vy.getValue()));    	
		
		if (vy.getValue() > 2 && !hasBursted) {
			middleRocket.setBursting(true);
			//System.out.println("vy < 0 => middleRocket burst ON!");
			System.out.println("middle on!");
			hasBursted = true;
		}
		
    }

}
