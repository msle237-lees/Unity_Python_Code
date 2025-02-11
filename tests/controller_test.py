import logging
import pygame

pygame.init()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up the pygame controller
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0)
joystick.init()

# Print the joystick name
logger.info("Joystick name: {}".format(joystick.get_name()))

# In while loop print raw joystick data
while True:
    for event in pygame.event.get():
        if event.type == pygame.JOYBUTTONDOWN:
            logger.info("Button: {}".format(event.button))
        if event.type == pygame.JOYAXISMOTION:
            logger.info("Axis: {} Value: {}".format(event.axis, event.value))
        if event.type == pygame.JOYHATMOTION:
            logger.info("Hat: {}".format(event.value))
    
    # Get the joystick data
    data = {
        "axes": [joystick.get_axis(i) for i in range(joystick.get_numaxes())],
        "buttons": [joystick.get_button(i) for i in range(joystick.get_numbuttons())],
        "hats": [joystick.get_hat(i) for i in range(joystick.get_numhats())]
    }

    # Log the data
    logger.info(data)