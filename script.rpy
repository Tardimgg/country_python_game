label start:

    "ewfyg" "start"


    init python:

        class View():
            def __init__(self, position, displayable, min_size=(0, 0), **kwargs):
                if "box_view" in kwargs:
                    kwargs["box_view"].addView(self)
                self._x = position[0]
                self._y = position[1]
                self._displayable = displayable
                self._min_size = (min_size[0], min_size[1])
                self._size = self._min_size


            def render(self, r, width, height, st, at):
                render_view = renpy.render(self._displayable, width, height, st, at)
                size = render_view.get_size()
                self._size = (max(size[0], self._min_size[0]), max(size[1], self._min_size[1]))
                r.blit(render_view, (self._x, self._y))


            def event(self, position, **kwargs):
                return False

            def get_displayable(self):
                return self._displayable

            def set_position(self, position):
                self._x, self._y = position[0], position[1]

            def get_position(self):
                return (self._x, self._y)

            def get_size(self):
                return self._size

            def exit(self):
                pass


        class ButtonView(View):

            def __init__(self, view, **kwargs):
                if "box_view" in kwargs:
                    kwargs["box_view"].addView(self)
                self._root_view = view

            def event(self, position, **kwargs):
                if "recursive_event" in kwargs:
                    self._root_view.event(position, kwargs=kwargs)
                x, y = self.get_position()
                size = self.get_size()
                return (x + size[0]) > position[0] > x and (y + size[1]) > position[1] > y

            def render(self, r, width, height, st, at):
                self._root_view.render(r, width, height, st, at)

            def get_position(self):
                return self._root_view.get_position()

            def get_view(self):
                return self._root_view

            def set_position(self, position):
                self._root_view.set_position(position)

            def get_size(self):
                return self._root_view.get_size()

            def exit(self):
                self._root_view.exit()




        class EditText(View):



            def __init__(self, start_text, position, max_symbol=float("inf"), **kwargs):
                if "box_view" in kwargs:
                    kwargs["box_view"].addView(self)
                self._start_text = start_text
                self._text = self._start_text
                self._cursor = "|"
                self._max_symbol = max_symbol
                self._text_view = Text("".join(self._text))
                self._position = position
                super(EditText, self).__init__(self._position, self._text_view, (max_symbol * 19.4, 0))
                self._text_button = ButtonView(self)
                self._update_cursor = EditText.UpdateCursor(1, self._render_add_function, self._render_remove_function, self)
                self._update_cursor.setDaemon(True)
                self._update_cursor.start()
                self._is_active = False


            def _render_add_function(self, parent):
                self._text_view.set_text(self._text + self._cursor)

            def _render_remove_function(self, parent):
                self._text_view.set_text(self._text)

            def set_position(self, position):
                super(EditText, self).set_position(position)
                self._position = position

            def get_position(self):
                return self._position


            def on_active(self):
                self._is_active = True
                self._update_cursor.resume()

            def off_active(self):
                self._is_active = False
                self._update_cursor.pause()

            def get_text(self):
                return self._text

            def event(self, position, symbol=None, backspace=False, **kwargs):
                if "position" in kwargs:
                    position = kwargs["position"]
                if "symbol" in kwargs:
                    symbol = kwargs["symbol"]
                if "backspace" in kwargs:
                    backspace = kwargs["backspace"]
                if symbol != None:
                    if self._is_active:
                        self._update_cursor.pause()
                        if backspace:
                            if len(self._text) > len(self._start_text):
                                self._text = self._text[:-1]
                                self._text_view.set_text(self._text)
                        elif len(self._text) < self._max_symbol:
                            self._text += symbol
                            self._text_view.set_text(self._text)
                        self._update_cursor.resume()
                elif self._text_button.event(position):
                    self._update_cursor.resume()
                    self.on_active()
                else:
                    self._update_cursor.pause()
                    self.off_active()


            def exit(self):
                self._update_cursor.exit()




            import threading

            class UpdateCursor(threading.Thread):

                import time

                def __init__(self, update_time, render_add_function, render_remove_function, parent):
                    import pygame, threading

                    super(EditText.UpdateCursor, self).__init__(self)
                    self._render_add_function = render_add_function
                    self._render_remove_function = render_remove_function
                    self._update_time = update_time
                    self._is_add_function = 0
                    self._is_work = True
                    self._parent = parent
                    self._clock = pygame.time.Clock()
                    self._event = threading.Event()

                def run(self):
                    while self._is_work:
                        if self._is_add_function:
                            self._event.wait()
                            self._render_add_function(self._parent)
                        else:
                            self._render_remove_function(self._parent)
                            self._event.wait()
                        self._is_add_function = not self._is_add_function
                        self._clock.tick(2)



                def exit(self):
                    self.resume()
                    self._is_work = False
                    super(UpdateCursor, self).exit()


                def pause(self):
                    self._event.clear()

                def resume(self):
                    self._event.set()


        class FieldView(View):
            def __init__(self, position, root_view, *views, **kwargs):
                if "box_view" in kwargs:
                    kwargs["box_view"].addView(self)
                self._child_view = []
                self._child_start_position = []
                self._view = root_view
                self._position = position
                super(FieldView, self).__init__(self._position, self._view)
                for value in views:
                    self._child_start_position.append(value.get_position())
                    self._child_view.append(value)
                self._set_child_position()

            def _set_child_position(self):
                for i in range(len(self._child_view)):
                    self._child_view[i].set_position((self._child_start_position[i][0] + self._position[0], self._child_start_position[i][1] + self._position[1]))

            def render(self, r, width, height, st, at):
                super(FieldView, self).render(r, width, height, st, at)
                for value in self._child_view:
                    value.render(r, width, height, st, at)

            def exit(self):
                super(FieldView, self).exit()
                for value in self._child_view:
                    value.exit()

            def event(self, position, **kwargs):
                answer = []
                for value in self._child_view:
                    answer.append(value.event(position, kwargs=kwargs))
                return answer

            def get_views(self):
                return self._child_view


            def set_position(self, position):
                self._position = position
                super(FieldView, self).set_position(position)
                self._set_child_position()

            def get_position(self):
                return self._position

            def get_size(self):
                return self._size



        class FlyView(View):

            def __init__(self, view, speed=5, **kwargs):
                if "box_view" in kwargs:
                    kwargs["box_view"].addView(self)
                self._root_view = view
                self._start_x, self._start_y = self._root_view.get_position()
                self._current_x = float(self._start_x)
                self._current_y = float(self._start_y)
                self._k_x = 1.0
                self._k_y = 1.0
                self._size = (0, 0)
                self._speed = speed
                self._stop = True
                self._last_coordinates = None
                self._end_position = None


            def render(self, r, width, height, st, at):
                if (not self._stop):
                    self._move()
                self._root_view.render(r, width, height, st, at)


            def get_end_position(self):
                return self._end_position

            def is_in_start(self):
                return abs(self._current_y - self._start_y) < self._speed

            def is_in_end(self):
                return self._stop and not self.is_in_start()

            def get_view(self):
                return self._root_view



            def _move(self):
                if abs(self._current_y - self._last_coordinates[1]) < self._speed and abs(self._current_x - self._last_coordinates[0]) < self._speed:
                    self._stop = True
                else:
                    self._current_x += self._k_x
                    self._current_y += self._k_y
                self._root_view.set_position((self._current_x, self._current_y))


            def event(self, position, **kwargs):
                return self._root_view.event(position, kwargs=kwargs)

            def get_position(self):
                return self._root_view.get_position()

            def set_position(self, position):
                self._current_x, self._current_y = position
                self._stop = True
                self._root_view.set_position(position)

            def get_size(self):
                return self._root_view.get_size()

            def get_view(self):
                return self._root_view

            def exit(self):
                self._root_view.exit()


            def fly(self, last_coordinates):
                if last_coordinates != None:
                    self._end_position = last_coordinates
                if (self._stop):
                    if last_coordinates == None:
                        last_coordinates = (self._start_x, self._start_y)
                    self._last_coordinates = last_coordinates
                    delta_x = abs(self._current_x - self._last_coordinates[0])
                    delta_y = abs(self._current_y - self._last_coordinates[1])
                    if delta_x > delta_y:
                        self._k_x = 1
                        self._k_y = float(abs(self._current_y - self._last_coordinates[1])) / abs(self._current_x - self._last_coordinates[0])
                    elif delta_x < delta_y:
                        self._k_x = float(abs(self._current_x - self._last_coordinates[0])) / abs(self._current_y - self._last_coordinates[1])
                        self._k_y = 1
                    else:
                        self._k_x = 1
                        self._k_y = 1
                    self._k_x *= 1 if self._current_x < self._last_coordinates[0] else -1
                    self._k_y *= 1 if self._current_y < self._last_coordinates[1] else -1
                    self._k_x *= self._speed
                    self._k_y *= self._speed
                    self._stop = False
                    self._move()
                    return True

                return False



        class BoxView:

            def __init__(self):
                self._views = []

            def addView(self, view):
                self._views.append(view)

            def render(self, r, width, height, st, at):
                for value in self._views:
                    value.render(r, width, height, st, at)

            def exit(self):
                for value in self._views:
                    value.exit()


        class GameDisplayable(renpy.Displayable):

            def __init__(self):

                import pygame

                renpy.Displayable.__init__(self)

                self._target_position = [(520, 95), (715, 145), (635, 195), (520, 245), (670, 295), (430, 345), (0, 0)]
                self._target_position_available = [True, True, True, True, True, True, True, True]

                self._box_view = BoxView()

                self._game_result = 0
                self._FPS = 60
                self._clock = pygame.time.Clock()
                self._exit_button = ButtonView(View((1050, 630), Text("Продолжить")), box_view=self._box_view)
                self._correct_answer = [["египет"], ["россия", "ссср"], ["италия"], ["франция"], ["украина", "ссср"], ["великобритания", "англия"]]


                self._list = 0



                self._1_image = FlyView(View((95, 150), Image("1_photo.jpg")), speed=10, box_view=self._box_view)
                self._2_image = FlyView(View((490, 150), Image("2_photo.jpg")), speed=10, box_view=self._box_view)
                self._3_image = FlyView(View((885, 150), Image("3_photo.jpg")), speed=10, box_view=self._box_view)
                self._4_image = FlyView(View((1375, 150), Image("4_photo.jpg")), speed=10, box_view=self._box_view)
                self._5_image = FlyView(View((1770, 150), Image("5_photo.jpg")), speed=10, box_view=self._box_view)
                self._6_image = FlyView(View((2165, 150), Image("6_photo.jpg")), speed=10, box_view=self._box_view)

                view_for_input_field_color = "#583613"

                self._text_input_for_1_image = FlyView(FieldView((104, 398), Solid(view_for_input_field_color, xsize=280, ysize=32), EditText("ст.", (5, 0), max_symbol=14)), speed=10, box_view=self._box_view)
                self._text_input_for_2_image = FlyView(FieldView((499, 398), Solid(view_for_input_field_color, xsize=280, ysize=32), EditText("ст.", (5, 0), max_symbol=14)), speed=10, box_view=self._box_view)
                self._text_input_for_3_image = FlyView(FieldView((894, 398), Solid(view_for_input_field_color, xsize=280, ysize=32), EditText("ст.", (5, 0), max_symbol=14)), speed=10, box_view=self._box_view)
                self._text_input_for_4_image = FlyView(FieldView((1384, 398), Solid(view_for_input_field_color, xsize=280, ysize=32),  EditText("ст.", (5, 0), max_symbol=14)), speed=10, box_view=self._box_view)
                self._text_input_for_5_image = FlyView(FieldView((1779, 398), Solid(view_for_input_field_color, xsize=280, ysize=32),  EditText("ст.", (5, 0), max_symbol=14)), speed=10, box_view=self._box_view)
                self._text_input_for_6_image = FlyView(FieldView((2174, 398), Solid(view_for_input_field_color, xsize=280, ysize=32),  EditText("ст.", (5, 0), max_symbol=14)), speed=10, box_view=self._box_view)

                self._text_input = [self._text_input_for_1_image, self._text_input_for_2_image, self._text_input_for_3_image, self._text_input_for_4_image, self._text_input_for_5_image, self._text_input_for_6_image]

                self._conveyor_image = View((0, 81), Image("conveyor.png"), box_view=self._box_view)

                self._box_1_image = FlyView(View((71, 129), Image("picture_frame.png")), speed=10, box_view=self._box_view)
                self._box_1_text = FlyView(View((71, 365), Image("text_frame.png")), speed=10, box_view=self._box_view)

                self._box_2_image = FlyView(View((466, 129), Image("picture_frame.png")), speed=10, box_view=self._box_view)
                self._box_2_text = FlyView(View((466, 365), Image("text_frame.png")), speed=10, box_view=self._box_view)

                self._box_3_image = FlyView(View((861, 129), Image("picture_frame.png")), speed=10, box_view=self._box_view)
                self._box_3_text = FlyView(View((861, 365), Image("text_frame.png")), speed=10, box_view=self._box_view)



                self._image = Image("tree.png")


            def render(self, width, height, st, at):
                r = renpy.Render(width, height)

                image = renpy.render(self._image, width, height, st, at)
                r.blit(image, (0, 500))


                self._box_view.render(r, width, height, st, at)

                self._clock.tick(self._FPS)
                renpy.redraw(self, 0)

                return r


            # Handles events.
            def event(self, ev, x, y, st):

                import pygame

                exit_game = False
                if ev.type == pygame.QUIT:
                    self._box_view.exit()


                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:

                    for value in self._text_input:
                        value.get_view().get_views()[0].event(position=(x, y))

                    if self._exit_button.event((x, y)) and self._list == 0:
                        self._1_image.fly((-350, 150))
                        self._2_image.fly((-350, 150))
                        self._3_image.fly((-350, 150))

                        self._text_input_for_1_image.fly((-350, 398))
                        self._text_input_for_2_image.fly((-350, 398))
                        self._text_input_for_3_image.fly((-350, 398))


                        self._4_image.fly((95, 150))
                        self._5_image.fly((490, 150))
                        self._6_image.fly((885, 150))

                        self._text_input_for_4_image.fly((104, 398))
                        self._text_input_for_5_image.fly((499, 398))
                        self._text_input_for_6_image.fly((894, 398))

                        self._list += 1
                    elif self._exit_button.event((x, y)):
                        exit_game = True
                        for i in range(len(self._text_input)):
                             if self._text_input[i].get_view().get_views()[0].get_text()[3:].lower().strip() in self._correct_answer[i]:
                                  self._game_result += 1


                if self._list == 1:
                    self._exit_button.get_view().get_displayable().set_text("Закончить")

                    renpy.restart_interaction()
                if ev.type == pygame.KEYDOWN:
                    for value in self._text_input:
                         value.get_view().get_views()[0].event(position=(x, y), symbol=ev.unicode, backspace=ev.key == pygame.K_BACKSPACE)


                if exit_game:
                    return self._game_result
                else:
                    raise renpy.IgnoreEvent()

    screen game():

        default word_game = GameDisplayable()

        add "background"

        add word_game


    label play_game:

        window hide
        $ quick_menu = False

        call screen game

        $ quick_menu = True
        window show

    show eileen vhappy


    "we4ftihu" "верно [_return]"

