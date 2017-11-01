import sys
import pygame

pygame.init()


class Bullet:

    def __init__(self, color=None):
        if color is None:
            color = [255, 255, 255]

        self.position = [-100, -100]
        self.velocity = [0, 0]

        # Load the image and resize it
        temp = pygame.image.load('bullet.bmp')
        self.img = pygame.transform.scale(temp, (20, 20))

        # Color the image
        arr = pygame.surfarray.pixels3d(self.img)
        arr[:, :, 0] = color[0]
        arr[:, :, 1] = color[1]
        arr[:, :, 2] = color[2]

        self.was_shot = False

    def reset_bullet(self):
        self.position = [-100, 100]
        self.velocity = [0, 0]
        self.was_shot = False

    def update(self, delta_t):
        if self.was_shot:
            self.position[0] += self.velocity[0] * delta_t
            self.position[1] += self.velocity[1] * delta_t

    def draw(self, scr):
        r = self.get_rect()
        scr.blit(self.img, r)

    def get_rect(self):
        r = self.img.get_rect()
        r.center = self.position
        return r


class Player:
    """
    Class for representing players in the game.

    Before creating an instance of this class, the video mode has to be set (e.g. by creating a Game instance).

    Attributes:
        - MAX_SPEED: Maximum speed for the player. Constant number.
        - SHOOTING_SPEED: Speed of the player's bullets when shot. Constant number.
        - img: Image of the player, used to draw it. Surface.
        - position: Position of the player. Array with two elements.
        - velocity: Velocity of the player. Array with two elements.
        - acceleration: Acceleration of the player. Array with two elements.
        - crosshair: Position of the player's crosshair. Array with two elements.
        - crosshair_img: Image of the player's crosshair. Surface.
        - bullet: The bullet of the player. Bullet object.
        - score: The player's score. Number.
        - decide_action: Function to decide the player's action, given a Game instance. Function that takes a game
        instance as argument, and returns a list of actions to be taken which will be interpreted by the update()
        method of this class.
    """

    def __init__(self, position=None, sz=None, img_filename='player.bmp', decide_action_fun=None,
                 player_color=None):
        """
        Initialize a player instance.

        :param position: Initial 2D position for the player. Default value is [0,0].
        :type position: List with two elements.
        :param sz: New size of the player's image after resizing. Default value None (no resizing).
        :type sz: Tuple with two elements.
        :param img_filename: Filename for the player's image. Default value is 'player.bmp'.
        :type img_filename: string
        :param decide_action_fun: Function that the will be called to decide the player's actions at each time step.
            Default value is a function that always returns no actions.
        :type decide_action_fun: Function that takes one argument, a Game instance, and returns a list of actions to be
            interpreted by the update() method.
        :param player_color: RGB color for the player. Default value is [255, 255, 255]
        :type player_color: Array with three values.
        """

        self.MAX_SPEED = 1500
        self.SHOOTING_SPEED = 3000

        # Default value for position
        if position is None:
            position = [0, 0]

        # Default value for color of the player
        if player_color is None:
            player_color = [255, 255, 255]

        # Velocity and acceleration initializations
        self.position = position
        self.velocity = [0, 0]
        self.acceleration = [0, 0]

        # Load image and optionally resize it
        temp = pygame.image.load(img_filename).convert()
        if sz is None:
            self.img = temp
        else:
            self.img = pygame.transform.scale(temp, sz)

        # Color the player image
        arr = pygame.surfarray.pixels3d(self.img)
        arr[:, :, 0] = player_color[0]
        arr[:, :, 1] = player_color[1]
        arr[:, :, 2] = player_color[2]

        # Crosshair initialization
        self.crosshair = [200, 200]
        temp = pygame.image.load('crosshair.bmp').convert()
        self.crosshair_img = pygame.transform.scale(temp, (70, 70))
        self.crosshair_img.set_colorkey((0, 0, 0))

        # Color the crosshair image
        arr = pygame.surfarray.pixels3d(self.crosshair_img)
        arr_r = arr[:, :, 0]
        arr_g = arr[:, :, 1]
        arr_b = arr[:, :, 2]
        arr_r[arr_r == 255] = player_color[0]
        arr_g[arr_g == 255] = player_color[1]
        arr_b[arr_b == 255] = player_color[2]

        # Bullet position initialization
        self.bullet = Bullet(player_color)

        # If no function for deciding actions is provided, specify one that always decides to not act
        if decide_action_fun is None:
            def no_action(game_instance):
                del game_instance # unused argument
                action_names = ['up', 'down', 'left', 'right', 'shoot',
                                'ch_up', 'ch_down', 'ch_left', 'ch_right', 'ch_mouse']
                actions = {}
                for action in action_names:
                    actions[action] = False
                return actions
            decide_action_fun = no_action
        self.decide_action = decide_action_fun

        # Points initialization
        self.score = 0

    def get_rect(self):
        """
        Return a newly-created Rect object, with it's `center` attribute at the same position as the player.

        Note: Changing this returned Rect has no effect on the Player instance.

        :return: Rectangle object, centered at the player.
        :rtype: Rect.
        """

        r = self.img.get_rect()
        r.center = (self.position[0], self.position[1])
        return r

    def update(self, actions, delta_t):
        """
        Update the state of the player, depending on which actions were taken in this time step.

        The `actions` parameter is a dictionary containing the following keys:
            - 'up': Accelerates the player upwards (True or False).
            - 'down': Accelerates the player downwards (True or False).
            - 'left': Accelerates the player to the left (True or False).
            - 'right': Accelerates the player to the right (True or False).
            - 'ch_up': Moves the player's crosshair up (True or False).
            - 'ch_down': Moves the player's crosshair down (True or False).
            - 'ch_left': Moves the player's crosshair left (True or False).
            - 'ch_right': Moves the player's crosshair right (True or False).
            - 'ch_mouse': Aligns the player's crosshair with the mouse (True or False).
            - 'shoot': Tries shooting the player's bullet (True or False).
        A key with value False means that the corresponding action will not be executed. If 'ch_mouse' is not False,
        all the other 'ch_*' actions are ignored.

        Player's move according to a simple discretized CA model. The action taken at time step 'i' influences directly
        the acceleration at time step 'i+1'.

        :param actions: Dictionary of actions that the player chose to take in this time step
        :type actions: Dictionary with keys of the type string
        :param delta_t: How much time passed since the last update
        :type delta_t: float
        """

        alpha = 20000
        k = 3000

        # Update position (CA model)
        self.position[0] += self.velocity[0] * delta_t + self.acceleration[0] * (delta_t ** 2) / 2
        self.position[1] += self.velocity[1] * delta_t + self.acceleration[1] * (delta_t ** 2) / 2

        # Update velocity (CA model)
        self.velocity[0] += self.acceleration[0] * delta_t
        self.velocity[1] += self.acceleration[1] * delta_t

        # Update acceleration
        thrust = [actions['right'] - actions['left'],
                  actions['down'] - actions['up']]
        thrust_mag = (thrust[0] ** 2 + thrust[1] ** 2) ** 0.5
        if thrust_mag > 0:
            self.acceleration[0] = alpha * thrust[0] / thrust_mag
            self.acceleration[1] = alpha * thrust[1] / thrust_mag
        else:
            self.acceleration = [0, 0]

        # Limit maximum speed
        speed = (self.velocity[0] ** 2 + self.velocity[1] ** 2) ** 0.5
        if speed > self.MAX_SPEED:
            limiting_factor = self.MAX_SPEED/speed
            self.velocity[0] *= limiting_factor
            self.velocity[1] *= limiting_factor

        # Threshold the velocities to zero (this makes the player stop eventually, if no acceleration is given)
        if speed < 30:
            self.velocity = [0, 0]

        # Add friction-like component
        if speed > 0.1:
            self.acceleration[0] -= self.velocity[0] / speed * k
            self.acceleration[1] -= self.velocity[1] / speed * k

        # Update crosshair position
        if actions['ch_mouse']:
            self.crosshair = pygame.mouse.get_pos()
        else:
            beta = 30
            self.crosshair[0] += beta * (actions['ch_right'] - actions['ch_left'])
            self.crosshair[1] += beta * (actions['ch_down'] - actions['ch_up'])

        # Shoot, if player chose this action
        if actions['shoot'] and not self.bullet.was_shot:

            # Compute bullet's velocity direction
            bullet_vel = [self.crosshair[0]-self.position[0], self.crosshair[1]-self.position[1]]

            # Adjust bullet's velocity magnitude
            bullet_speed = (bullet_vel[0] ** 2 + bullet_vel[1] ** 2) ** 0.5
            bullet_vel[0] *= self.SHOOTING_SPEED / bullet_speed
            bullet_vel[1] *= self.SHOOTING_SPEED / bullet_speed

            # Set the bullet's attributes
            self.bullet.position = self.position[:]
            self.bullet.velocity = bullet_vel
            self.bullet.was_shot = True

        self.bullet.update(delta_t)

    def draw(self, scr):
        """
        Draw the player, its crosshair, and its bullet in the Surface object provided as argument.

        :param scr: Where the player and it's crosshair will be drawn.
        :type scr: Surface.
        """

        # Draw the player
        scr.blit(self.img, self.get_rect())

        # Draw its crosshair
        r_crosshair = self.crosshair_img.get_rect()
        r_crosshair.center = self.crosshair
        scr.blit(self.crosshair_img, r_crosshair)

        # Draw its bullet
        self.bullet.draw(scr)


import numpy as np
class Game:
    """
    Class for representing the move n' shoot game.

    Attributes:
        - screen_width: Width of the screen used to draw the game. Number.
        - screen_height: Width of the screen used to draw the game. Number.
        - screen: The screen of the game, where it will be drawn. Surface object.
        - clock: Clock to hold the game's time information. Clock object.
        - key_pressed: Dictionary with one key for each recognized keyboard key the user can press. The values are
            either True or False, depending on whether that key was being pressed or not when the handle_events()
            method was last called.
        - players: Holds all the players present in the game. Array of Player objects.
    """

    def __init__(self, screen_sz=None):
        """
        Initializes a game instance.

        :param screen_sz: Tuple that represents the width and height of the screen that will be created. Default value
            is (1600,800).
        :type screen_sz: Tuple with two elements.
        """
        if screen_sz is None:
            screen_sz = (1600, 800)

        self.screen_width = screen_sz[0]
        self.screen_height = screen_sz[1]
        self.screen = pygame.display.set_mode(screen_sz)
        self.clock = pygame.time.Clock()

        # Initialize dictionary for key presses and mouse clicks
        self.key_pressed = {}
        for key in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_DOWN, pygame.K_UP,
                    pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_SPACE, 'mouse_click']:
            self.key_pressed[key] = False

        # Initialize player's array
        self.players = []

        # Initialize font used in the game
        pygame.font.init()
        self.my_font = pygame.font.SysFont('Monospace', 40)

    def add_player(self, decide_action_fun=None, position=None, player_color=None):
        """
        Adds a new player to the game. Maximum 2 players in the game.

        :param decide_action_fun: Function that the player will use to decide its actions
        :type decide_action_fun: Function that takes a Game instance as argument, and outputs a list of actions, to be
            interpreted by the players update() method.
        :param position: Initial position for the player being added to the game. Default value is [0,0].
        :type position: Array with two elements.
        :param player_color: RGB color of the player being added. Default value is [255, 255, 255]
        :type player_color: Array with three elements.
        """

        if len(self.players) < 2:
            self.players.append(Player(position, decide_action_fun=decide_action_fun, player_color=player_color))

    def handle_events(self):
        """
        Handles all events from the game (quitting, updating key presses, mouse clicks, etc).
        """
        for event in pygame.event.get():

            # Handle closing event
            if event.type == pygame.QUIT:
                sys.exit()

            # Handle key presses
            if event.type == pygame.KEYDOWN:
                if event.key in self.key_pressed:
                    self.key_pressed[event.key] = True

            # Handle key releases
            if event.type == pygame.KEYUP:
                if event.key in self.key_pressed:
                    self.key_pressed[event.key] = False

            # Handle mouse clicks
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.key_pressed['mouse_click'] = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.key_pressed['mouse_click'] = False

    def update_physics(self):
        """
        Updates the game's current state, using all the player's actions and the game's physics.

        Every player will have the decide_action() method called to determine its actions, and then the update() method
        to perform these.

        Physics:
            - Crosshair position is limited to the screen.
            - Player's position is limited to the screen.
            - Partially elastic collision between players and the borders of the screen.
            - Perfectly elastic collision between players.
        """
        delta_t = 1/60

        # For each player
        for i, player in enumerate(self.players):

            # Decide actions for player
            actions = player.decide_action(self)

            # Update player using chosen actions
            player.update(actions, delta_t)

            # Limit crosshair position
            if player.crosshair[0] < 0:
                player.crosshair[0] = 0
            if player.crosshair[0] > self.screen_width:
                player.crosshair[0] = self.screen_width
            if player.crosshair[1] < 0:
                player.crosshair[1] = 0
            if player.crosshair[1] > self.screen_height:
                player.crosshair[1] = self.screen_height

            # Check collisions with walls
            r = player.get_rect()
            if r.left < 0:
                player.position[0] = r.width / 2
                player.velocity[0] = -player.velocity[0]*0.8
            if r.top < 0:
                player.position[1] = r.height / 2
                player.velocity[1] = -player.velocity[1]*0.8
            if r.right > self.screen_width:
                player.position[0] = self.screen_width - r.width / 2
                player.velocity[0] = -player.velocity[0]*0.8
            if r.bottom > self.screen_height:
                player.position[1] = self.screen_height - r.height / 2
                player.velocity[1] = -player.velocity[1]*0.8

            # Check bullet collision with walls
            r = player.bullet.get_rect()
            if r.right < 0 or r.bottom < 0 or r.left > self.screen_width or r.top > self.screen_height:
                player.bullet.reset_bullet()

            # Check bullet collision with the other player
            if r.colliderect(self.players[1-i].get_rect()):
                player.score += 1
                player.bullet.reset_bullet()

        # Parse collision between players (if there are two players in the game)
        if len(self.players) == 2:
            self.__parse_player_collision(self.players[0], self.players[1])

    def __parse_player_collision(self, player1, player2):
        """
        Checks if player 1 and 2 are colliding. If they are, resolve the collision by updating their positions and
        velocities using a perfectly elastic collision model. This is accomplished by using the players' current states
        (in which their Rects intersect) to estimate the states exactly at the moment of collision (using a constant
        velocity model).

        Assumptions:
            - Both players' Rects are squares.
            - Both players' Rects have the same side length.
            - Players velocity did not change since the last call of this function.
            - Players have the same mass.
            - The collision between players is perfectly elastic.

        Note 1: The assumption about constant player velocity might be broken without many complications, if this
        function is called frequently enough.
        Note 2: estimation could (?) be better using the players' accelerations as well, but also more computationally
        expensive. However, if this method is called frequently enough, this should not matter.

        :param player1: The first player involved in the collision.
        :type player1: Player.
        :param player2: The second player involved in the collision.
        :type player2: Player.
        """

        # Initializations
        r1 = player1.get_rect()
        r2 = player2.get_rect()
        l = player1.get_rect().width

        # If the collision happened, parse it
        if r1.colliderect(r2):

            is_collision_x = is_collision_y = False

            # Use the players' position to determine the length of the intersection between them in x and y
            delta_x = l - abs(player1.position[0] - player2.position[0])
            delta_y = l - abs(player1.position[1] - player2.position[1])

            # Use the players' velocities to determine how long ago would a collision have happened in each of the
            # directions
            v_x = abs(player1.velocity[0] - player2.velocity[0])
            v_y = abs(player1.velocity[1] - player2.velocity[1])
            delta_tx = delta_x / v_x if v_x > 0 else float('inf')
            delta_ty = delta_y / v_y if v_y > 0 else float('inf')

            # The collision likely happened in the direction with the smallest delta_t
            if delta_tx < delta_ty:
                is_collision_x = True
            elif delta_ty < delta_tx:
                is_collision_y = True
            else:
                is_collision_x = is_collision_y = True

            # Change players' positions to where they were right before impact
            delta_t = min(delta_tx, delta_ty)
            player1.position[0] -= player1.velocity[0] * delta_t
            player1.position[1] -= player1.velocity[1] * delta_t
            player2.position[0] -= player2.velocity[0] * delta_t
            player2.position[1] -= player2.velocity[1] * delta_t

            # Change players' velocities depending on the direction of the collision
            for i, collision in enumerate((is_collision_x, is_collision_y)):
                if collision:
                    # Switch players' velocities in this direction
                    (player1.velocity[i], player2.velocity[i]) = (player2.velocity[i], player1.velocity[i])

    def draw_frame(self):
        """
        Draws the current game state to the screen. Limited to max 60 fps.
        """
        # Black background
        self.screen.fill((0, 0, 0))

        # Draw all players
        for player in self.players:
            player.draw(self.screen)

        # Draw players' scores
        score_player1 = self.my_font.render('P1: ' + str(self.players[0].score), False, (255, 255, 255))
        score_player2 = self.my_font.render('P2: ' + str(self.players[1].score), False, (255, 255, 255))
        self.screen.blit(score_player1, (0, 0))
        self.screen.blit(score_player2, (0, 40))

        # Flip the display and limit frame-rate
        pygame.display.flip()
        self.clock.tick(60)

    @staticmethod
    def create_human_player_binding():
        """
        Used to create key-presses bindings to a player.

        The player's movement is bound to the keys up, down, left and right. Shooting is bound to the space key. Also,
        always moves the player's crosshair to the current mouse position.

        :return: Function that binds key presses and mouse movement to the player's actions. To be passed to the Player
            constructor class as the 'decide_action_fun' argument.
        :rtype: Function that takes a Game instance as argument, and returns a list of actions to be taken at each time
            step.
        """
        def fun(game_instance):
            action_names = ['up', 'down', 'left', 'right', 'shoot']
            key_bindings = [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT, 'mouse_click']
            actions = {}
            for action_name, key_binding in zip(action_names, key_bindings):
                actions[action_name] = game_instance.key_pressed[key_binding]

            actions['ch_mouse'] = True
            return actions
        return fun

    @staticmethod
    def create_random_player_binding(prob_action=0.05):

        def fun(game_instance):
            action_names = ['up', 'down', 'left', 'right', 'shoot', 'ch_up', 'ch_down', 'ch_left', 'ch_right']

            # Initialize old actions
            if not hasattr(fun, 'old_actions'):
                fun.old_actions = {}
                for action in action_names:
                    fun.old_actions[action] = False

            # For each action
            actions = {}
            for action in action_names:

                # With probability 'prob_action', do the opposite of what was done in the last call of this function
                r = np.random.rand()
                if r < prob_action:
                    actions[action] = not fun.old_actions[action]
                else:
                    actions[action] = fun.old_actions[action]

            # Don't use the mouse
            actions['ch_mouse'] = False

            # Update the old actions
            fun.old_actions = actions.copy()

            return actions

        return fun

    @staticmethod
    def create_simple_ai_binding(prob_action=0.05):

        def fun(game_instance):
            action_names = ['up', 'down', 'left', 'right', 'shoot']

            # Initialize old actions
            if not hasattr(fun, 'old_actions'):
                fun.old_actions = {}
                for action in action_names:
                    fun.old_actions[action] = False

            # For each action
            actions = {}
            for action in action_names:

                # With probability 'prob_action', do the opposite of what was done in the last call of this function
                r = np.random.rand()
                if r < prob_action:
                    actions[action] = not fun.old_actions[action]
                else:
                    actions[action] = fun.old_actions[action]

            # Don't use the mouse
            actions['ch_mouse'] = False

            # Make crosshair follow opponent
            actions['ch_left'] = game_instance.players[0].position[0] < game_instance.players[1].crosshair[0]
            actions['ch_right'] = game_instance.players[0].position[0] > game_instance.players[1].crosshair[0]
            actions['ch_up'] = game_instance.players[0].position[1] < game_instance.players[1].crosshair[1]
            actions['ch_down'] = game_instance.players[0].position[1] > game_instance.players[1].crosshair[1]

            # Update the old actions
            fun.old_actions = actions.copy()

            return actions

        return fun

teal_color = [0, 188, 212]
yellowish_color = [255, 235, 59]
max_score = 10

myGame = Game()
myGame.add_player(Game.create_human_player_binding(), [100, 100], teal_color)
myGame.add_player(Game.create_simple_ai_binding(), [myGame.screen_width, myGame.screen_height], yellowish_color)

while (myGame.players[0].score < max_score) and (myGame.players[1].score < max_score):
    myGame.handle_events()
    myGame.update_physics()
    myGame.draw_frame()

print('Final score')
print('Player 1:', myGame.players[0].score)
print('Player 2:', myGame.players[1].score)


