import arcade
import os

# Constants
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 650
SCREEN_TITLE = "Big Red In The Hood"

# Constants used to scale our sprites from their original size
CHARACTER_SCALING = 2
TILE_SCALING = 2
SPRITE_PIXEL_SIZE = 18
GRID_PIXEL_SIZE = SPRITE_PIXEL_SIZE * TILE_SCALING

# Movement speed of player, in pixels per frame
PLAYER_MOVEMENT_SPEED = 6
GRAVITY = 1
PLAYER_JUMP_SPEED = 20

# Player starting position
PLAYER_START_X = 64
PLAYER_START_Y = 425

ENEMY_START_X = 100
ENEMY_START_Y = 425

# Constants used to track if the player is facing left or right
RIGHT_FACING = 0
LEFT_FACING = 1

# Layer Names from our TileMap
LAYER_NAME_PLATFORMS = "Platforms"
LAYER_NAME_COINS = "Coins"
LAYER_NAME_FOREGROUND = "Foreground"
LAYER_NAME_BACKGROUND = "Background"
LAYER_NAME_DONT_TOUCH = "Dont Touch"
LAYER_NAME_LADDERS = "Ladders"
LAYER_NAME_MOVING_PLATFORMS = "Moving Platforms"
LAYER_NAME_PLAYER = "Player"
LAYER_NAME_ENEMY = "Enemy"

# Game States
GAME_RUNNING = 0
GAME_INTRO = 1


def load_texture_pair(filename):
    """
    Load a texture pair, with the second being a mirror image.
    """
    return [
        arcade.load_texture(filename),
        arcade.load_texture(filename, flipped_horizontally=True),
    ]


class PlayerCharacter(arcade.Sprite):
    """Player Sprite"""

    def __init__(self):

        # Set up parent class
        super().__init__()

        # Default to face-right
        self.character_face_direction = RIGHT_FACING

        # Used for flipping between image sequences
        self.cur_texture = 0
        self.scale = CHARACTER_SCALING

        # Track our state
        self.jumping = False
        self.climbing = False
        self.is_on_ladder = False

        # Sets main path for smaller line lengths and its more efficent
        main_path = "./Assets/Characters/Adventurer/Individual Sprites/adventurer-"

        # Load textures for idle standing
        self.idle_texture_pair = load_texture_pair(f"{main_path}idle-00.png")
        self.jump_texture_pair = load_texture_pair(f"{main_path}jump-00.png")
        self.fall_texture_pair = load_texture_pair(f"{main_path}fall-00.png")

        # Load textures for walking
        self.wallk_textures = []
        for i in range(6):
            texture = load_texture_pair(f"{main_path}run-{i}.png")
            self.walk_textures.append(texture)

        # Load textures for climbing
        self.climbing_textures = []
        texture = arcade.load_texture(f"{main_path}crnr-clmb-00.png")
        self.climbing_textures.append(texture)
        texture = arcade.load_texture(f"{main_path}crnr-clmb-01.png")
        self.climbing_textures.append(texture)

        # Set the initial texture
        self.texture = self.idle_texture_pair[0]

        # Set hitbox
        self.hit_box = self.texture.hit_box_points

    def update_animation(self, delta_time: float = 1 / 60):

        # Figure out what way the character is facing
        if self.change_x < 0 and self.character_face_direction == RIGHT_FACING:
            self.character_face_direction = LEFT_FACING
        elif self.change_x > 0 and self.character_face_direction == LEFT_FACING:
            self.character_face_direction = RIGHT_FACING

        # Climbing animation
        if self.is_on_ladder:
            self.climbing = True
        if not self.is_on_ladder and self.climbing:
            self.climbing = False
        if self.climbing and abs(self.change_y) > 1:
            self.cur_texture += 1
            if self.cur_texture > 5:
                self.cur_texture = 0
        if self.climbing:
            self.texture = self.climbing_textures[self.cur_texture // 4]
            return

        # Jumping animation
        if self.change_y > 0 and not self.is_on_ladder:
            self.texture = self.jump_texture_pair[
                self.character_face_direction]
            return
        elif self.change_y < 0 and not self.is_on_ladder:
            self.texture = self.fall_texture_pair[
                self.character_face_direction]
            return

        # Idle animation
        if self.change_x == 0:
            self.texture = self.idle_texture_pair[
                self.character_face_direction]
            return

        # Walking animation
        self.cur_texture += 1
        if self.cur_texture > 5:
            self.cur_texture = 0
        self.texture = self.walk_textures[self.cur_texture][
            self.character_face_direction]


class MyGame(arcade.Window):
    """
    Main application class.
    """

    def __init__(self):

        # Call the parent class and set up the window
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        # Set the path to start with this program
        file_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(file_path)

        # Set timer values as zero
        self.timer = 0
        self.time_elapsed = 0

        # Track the current state of what key is pressed
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False
        self.jump_needs_reset = False

        # Our TileMap Object
        self.tile_map = None

        # Initialize lives count
        self.lives_count = 3

        # Our Scene Object
        self.scene = None

        # Separate variable that holds the player sprite
        self.player_sprite = None

        # Our physics engine
        self.physics_engine = None

        # A Camera that can be used for scrolling the screen
        self.camera = None

        # Adding Sounds
        self.jump_sound = arcade.load_sound(
            ":resources:sounds/jump1.wav")

        # A Camera that can be used to draw GUI elements
        self.gui_camera = None

        # Where is the right edge of the map
        self.end_of_map = 0

        # Level
        self.level = 1

        # Game state
        self.game_state = GAME_INTRO

        # Set background colour
        arcade.set_background_color(arcade.csscolor.CORNFLOWER_BLUE)

    def setup(self):
        """
        Set up the game here. 
        Call this function to restart the game.
        """

        # Set up the Cameras
        self.camera = arcade.Camera(self.width, self.height)
        self.gui_camera = arcade.Camera(self.width, self.height)

        file_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(file_path)
        # Name of map file to load

        map_name = f"map_{self.level}.tmx"

        # Layer specific options are defined based on Layer names
        layer_options = {
            LAYER_NAME_PLATFORMS: {
                "use_spatial_hash": True,
            },
            LAYER_NAME_COINS: {
                "use_spatial_hash": True,
            },
            LAYER_NAME_DONT_TOUCH: {
                "use_spatial_hash": True,
            },
            LAYER_NAME_MOVING_PLATFORMS: {
                "use_spatial_hash": False,
            },
            LAYER_NAME_LADDERS: {
                "use_spatial_hash": True,
            },
            LAYER_NAME_COINS: {
                "use_spatial_hash": True,
            },
        }

        # Read in the tiled map
        self.tile_map = arcade.load_tilemap(
            map_name, TILE_SCALING, layer_options)
        self.end_of_map = self.tile_map.width * GRID_PIXEL_SIZE

        # Initialize Scene with our TileMap
        self.scene = arcade.Scene.from_tilemap(self.tile_map)
        self.scene.add_sprite_list_after(
            "Player", LAYER_NAME_FOREGROUND)

        # Add Player Spritelist before "Foreground" layer.
        self.scene.add_sprite_list_after(
            "Player", LAYER_NAME_FOREGROUND)

        # Set up the player
        self.player_sprite = PlayerCharacter()
        self.player_sprite.center_x = PLAYER_START_X
        self.player_sprite.center_y = PLAYER_START_Y
        self.scene.add_sprite("Player", self.player_sprite)

        # Set the background color
        if self.tile_map.background_color:
            arcade.set_background_color(self.tile_map.background_color)

        # Create the 'physics engine'
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite,
            platforms=self.scene[LAYER_NAME_MOVING_PLATFORMS],
            gravity_constant=GRAVITY,
            ladders=self.scene[LAYER_NAME_LADDERS],
            walls=self.scene[LAYER_NAME_PLATFORMS]
        )

    def draw_intro_screen(self):
        """Draw the introductory screen."""
        arcade.draw_text("Welcome to Big Red In The Hood", 
        SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100, 
        arcade.color.WHITE, 30, anchor_x="center")
        arcade.draw_text("Instructions:", 
        SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50, 
        arcade.color.WHITE, 20, anchor_x="center")
        arcade.draw_text("- Use arrow keys or WASD to move", 
        SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20, 
        arcade.color.WHITE, 16, anchor_x="center")
        arcade.draw_text("- Reach the end of the map to advance", 
        SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 10, 
        arcade.color.WHITE, 16, anchor_x="center")
        arcade.draw_text("Press Space to Start", 
        SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50, 
        arcade.color.WHITE, 20, anchor_x="center")

    def on_draw(self):
        """Render the screen."""
        arcade.start_render()

        # Runs the intro screen for the game
        if self.game_state == GAME_INTRO:
            self.draw_intro_screen()
            return

        # Draw the timer in the top left corner
        arcade.draw_text(f"Timer: {self.timer}", 10, 
        self.height - 20, arcade.color.WHITE, 14)

        # Draw the life count in the top left corner
        arcade.draw_text(f"Lives: {self.lives_count}", 10, 
        self.height - 40, arcade.color.WHITE, 14)

        # Activate the game camera
        self.camera.use()

        # Draw our Scene
        self.scene.draw(pixelated=True)

        # Activate the GUI camera before drawing GUI elements
        self.gui_camera.use()

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed."""
        if self.game_state == GAME_INTRO:
            if key == arcade.key.SPACE:
                self.game_state = GAME_RUNNING
                self.setup()
        else:
            if key == arcade.key.UP or key == arcade.key.W:
                self.up_pressed = True
            elif key == arcade.key.DOWN or key == arcade.key.S:
                self.down_pressed = True
            elif key == arcade.key.LEFT or key == arcade.key.A:
                self.left_pressed = True
            elif key == arcade.key.RIGHT or key == arcade.key.D:
                self.right_pressed = True
            self.process_keychange()

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key."""
        if self.game_state == GAME_RUNNING:
            if key == arcade.key.UP or key == arcade.key.W:
                self.up_pressed = False
                self.jump_needs_reset = False
            elif key == arcade.key.DOWN or key == arcade.key.S:
                self.down_pressed = False
            elif key == arcade.key.LEFT or key == arcade.key.A:
                self.left_pressed = False
            elif key == arcade.key.RIGHT or key == arcade.key.D:
                self.right_pressed = False
            self.process_keychange()

    def process_keychange(self):
        """
        Called when we change a key up/down or we move on/off a ladder.
        """
        # Process up/down while not on ladder
        if self.up_pressed and not self.down_pressed:
            if self.physics_engine.is_on_ladder():
                self.player_sprite.change_y = PLAYER_MOVEMENT_SPEED
            elif (
                self.physics_engine.can_jump(y_distance=10)
                and not self.jump_needs_reset
            ):
                self.player_sprite.change_y = PLAYER_JUMP_SPEED
                self.jump_needs_reset = True
                arcade.play_sound(self.jump_sound)
        elif self.down_pressed and not self.up_pressed:
            if self.physics_engine.is_on_ladder():
                self.player_sprite.change_y = -PLAYER_MOVEMENT_SPEED

        # Process up/down when on a ladder and no movement
        if self.physics_engine.is_on_ladder():
            if not self.up_pressed and not self.down_pressed:
                self.player_sprite.change_y = 0
            elif self.up_pressed and self.down_pressed:
                self.player_sprite.change_y = 0

        # Process left/right
        if self.right_pressed and not self.left_pressed:
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED
        elif self.left_pressed and not self.right_pressed:
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED
        else:
            self.player_sprite.change_x = 0

    def center_camera_to_player(self):
        """Centers camera to player character."""
        screen_center_x = self.player_sprite.center_x - (
            self.camera.viewport_width / 2)
        screen_center_y = self.player_sprite.center_y - (
            self.camera.viewport_height / 2)

        if screen_center_x < 0:
            screen_center_x = 0
        if screen_center_y < 0:
            screen_center_y = 0
        player_centered = screen_center_x, screen_center_y

        self.camera.move_to(player_centered, 0.2)

    def on_update(self, delta_time):
        """Update the game."""
        if self.game_state != GAME_RUNNING:
            return

        # Move the player with the physics engine
        self.physics_engine.update()

        # Will increment the timer 
        self.time_elapsed += delta_time  
        if self.time_elapsed >= 1.0:  
            self.timer += 1  
            self.time_elapsed -= 1.0 

        # Update walls, used with moving platforms
        self.scene.update([LAYER_NAME_MOVING_PLATFORMS])

        # Update animations
        if self.physics_engine.can_jump():
            self.player_sprite.can_jump = False
        else:
            self.player_sprite.can_jump = True

        if self.physics_engine.is_on_ladder() and not self.physics_engine.can_jump():
            self.player_sprite.is_on_ladder = True
            self.process_keychange()
        else:
            self.player_sprite.is_on_ladder = False
            self.process_keychange()

        # Update Animations
        self.scene.update_animation(
            delta_time, [LAYER_NAME_BACKGROUND, LAYER_NAME_PLAYER]
        )

        # Did the player fall off the map?
        if self.player_sprite.center_y < -100:
            self.player_sprite.center_x = PLAYER_START_X
            self.player_sprite.center_y = PLAYER_START_Y
            self.lives_count -= 1


        # Did the player touch something they should not?
        if arcade.check_for_collision_with_list(
            self.player_sprite, self.scene[LAYER_NAME_DONT_TOUCH]
        ):
            self.player_sprite.change_x = 0
            self.player_sprite.change_y = 0
            self.player_sprite.center_x = PLAYER_START_X
            self.player_sprite.center_y = PLAYER_START_Y
            self.lives_count -= 1

        # Check if player died 3 times
        if self.lives_count == 0:
            self.game_over()

        # See if the user got to the end of the level
        if self.player_sprite.center_x >= self.end_of_map:
            # Advance to the next level
            if self.level == 3:
                self.congratulations_screen()
            else:
                self.level = self.level + 1
                self.setup()

        # Position the camera
        self.center_camera_to_player()

    def congratulations_screen(self):
        """
        Will print a congratulations screen at the end of the game.
        """
        # Draws the congratulations screen. Will stay for 3 seconds
        arcade.set_background_color(arcade.color.BLACK)
        arcade.draw_text("Congratulations!", SCREEN_WIDTH / 2, 
        SCREEN_HEIGHT / 2, arcade.color.WHITE, 50, anchor_x="center")
        arcade.finish_render()  
        arcade.pause(3)
        # Closes the game window
        arcade.close_window()

    def game_over(self):
        """
        Game over screen for if the user dies 3 times.
        """
        # Draws the Game Over screen. Will stay for 3 seconds
        arcade.set_background_color(arcade.color.BLACK)
        arcade.draw_text("Game Over", SCREEN_WIDTH / 2, 
        SCREEN_HEIGHT / 2, arcade.color.WHITE, 50, anchor_x="center")
        arcade.finish_render()
        arcade.pause(3)  
        # Close the game window
        arcade.close_window()


def main():
    """Main function"""
    window = MyGame()
    arcade.run()


if __name__ == "__main__":
    main()
