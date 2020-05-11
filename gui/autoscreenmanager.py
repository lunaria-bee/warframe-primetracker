from kivy.core.window import Window
from kivy.properties import DictProperty
from kivy.uix.screenmanager import\
    ScreenManager, Screen,\
    CardTransition, FallOutTransition, RiseInTransition, SlideTransition


def get_reverse_transition(transition):
    '''Get the reverse of `transition`.

    PARAMETERS
    transition: Transition to get the reverse of.

    RETURN The reverse of `transition`.

    '''
    if isinstance(transition, SlideTransition):
        direction = {
            'left': 'right',
            'right': 'left',
            'up': 'down',
            'down': 'up'
        }[transition.direction]

        if isinstance(transition, CardTransition):
            mode = {
                'push': 'pop',
                'pop': 'push',
            }[transition.mode]
            reverse_transition = CardTransition()
            reverse_transition.direction = direction
            reverse_transition.mode = mode
        else:
            reverse_transition = SlideTransition(direction=direction)

    elif isinstance(transition, RiseInTransition):
        reverse_transition = FallOutTransition()

    elif isinstance(transition, FallOutTransition):
        reverse_transition = RiseInTransition()

    else:
        reverse_transition = transition

    return reverse_transition


class AutoScreenManager(ScreenManager):
    '''Screen manager that automatically handles screens and transitions.'''

    _transitions = DictProperty()
    '''Map of (screen name -> transition).

    Transition is the transition that was used when switching to that screen.

    '''

    # TODO keyboard stack?

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

        self.property('_transitions').link(self, '_transitions')

    def _keyboard_closed(self):
        print(self, '_keyboard_closed')
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        print(self, '_on_keyboard_down', keyboard, keycode, text, modifiers)
        if keycode[1] == 'escape':
            print('escape')
            # If there is no screen to reverse to, False will be returned, and the event
            # will continue up the stack
            # TODO event should actually continue up the stack
            return self.reverse()

    def switch_to_widget(self, widget, *args, transition=None, **kwargs):
        '''Create a screen containing widget and switch to that screen.

        PARAMETERS
        widget: The widget to display.
        transition: The transition to use when switching the screen. Options. If ommitted,
                    the current value of self.transition will be automatically used.

        '''
        if not transition is None:
            previous_transition = self.transition
            self.transition = transition

        screen = Screen(name='{}_{}'.format(widget.__class__.__name__, id(widget)))
        screen.add_widget(widget)
        self.add_widget(screen)
        self.current = screen.name

        self.property('_transitions').get(self)[self.current] = self.transition

        if not transition is None:
            self.transition = previous_transition

    def reverse(self, transition=None):
        '''Go back to the previous screen.

        If there is no previous screen to return to, do nothing.

        PARAMETERS
        transition: The transition to use when switching screens. Optional. If omitted,
                    the reverse of the transition that was used to switch to the current
                    screen will be automatically used.

        RETURN Whether the manager successfully returned to a previous screen.

        '''
        if len(self.screen_names) > 1:
            if self.property('_transitions').get(self)[self.current]:
                previous_transition = self.transition
                self.transition = get_reverse_transition(self.property('_transitions')
                                                         .get(self)[self.current])

            self.current = self.screen_names[-2]
            self.remove_widget(self.get_screen(self.screen_names[-1]))

            if self.property('_transitions').get(self)[self.current]:
                self.transition = previous_transition

            return True

        else:
            return False
