from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Rectangle, Ellipse
from kivy.uix.popup import Popup
from kivy.uix.colorpicker import ColorPicker
from kivy.core.window import Window
from kivy.uix.button import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from math import sqrt

class LineObject:
    def __init__(self, start_pos, end_pos, line):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.line = line

class EllipseObject:
    def __init__(self, pos, size, ellipse):
        self.pos = pos
        self.size = size
        self.ellipse = ellipse

class DrawingWidget(Widget):
    def __init__(self, **kwargs):
        super(DrawingWidget, self).__init__(**kwargs)
        self.current_angle = 0
        self.shape_color = (0, 0, 0)
        self.start_pos = None
        self.last_end_pos = None
        self.first_start_pos = None
        self.lines = []
        self.ellipses = []
        self.undo_stack = []
        self.is_erasing = False

        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos)

        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def on_touch_down(self, touch):
        if touch.button == 'left':
            if self.is_erasing:
                self.erase_at(touch.x, touch.y)
            else:
                if self.last_end_pos is None:
                    self.start_pos = (touch.x, touch.y)
                    self.first_start_pos = self.start_pos
                else:
                    self.start_pos = self.last_end_pos

    def on_touch_up(self, touch):
        if touch.button == 'left' and self.start_pos and not self.is_erasing:
            end_pos = (touch.x, touch.y)

            if self.first_start_pos:
                dist_to_first = sqrt((end_pos[0] - self.first_start_pos[0]) ** 2 +
                                     (end_pos[1] - self.first_start_pos[1]) ** 2)
                if dist_to_first < 20:
                    end_pos = self.first_start_pos

            with self.canvas:
                Color(*self.shape_color)
                x1, y1 = self.start_pos
                x2, y2 = end_pos

                ellipse = Ellipse(pos=(x1 - 3, y1 - 3), size=(6, 6))
                ellipse_obj = EllipseObject((x1, y1), (6, 6), ellipse)
                self.ellipses.append(ellipse_obj)

                if self.current_angle == 0:
                    line = Line(points=[x1, y1, x2, y1])
                    self.last_end_pos = (x2, y1)
                elif self.current_angle == 45:
                    line = Line(points=[x1, y1, x2, y2])
                    self.last_end_pos = (x2, y2)
                elif self.current_angle == 90:
                    line = Line(points=[x1, y1, x1, y2])
                    self.last_end_pos = (x1, y2)

                line_obj = LineObject(self.start_pos, end_pos, line)
                self.lines.append(line_obj)
                self.undo_stack.append((line_obj, ellipse_obj))

            self.start_pos = None

    def set_angle(self, angle):
        self.current_angle = angle
        if self.is_erasing:
            self.is_erasing = False

    def set_color(self, color):
        self.shape_color = color

    def clear_canvas(self):
        self.canvas.clear()
        self.last_end_pos = None
        self.first_start_pos = None
        self.lines.clear()
        self.ellipses.clear()
        self.undo_stack.clear()

        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

    def erase_at(self, x, y):
        threshold_distance = 10
        lines_to_remove = []
        ellipses_to_remove = []

        def point_line_distance(px, py, x1, y1, x2, y2):
            if (x1 == x2) and (y1 == y2):
                return sqrt((px - x1) ** 2 + (py - y1) ** 2)
            dx = x2 - x1
            dy = y2 - y1
            t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
            t = max(0, min(1, t))
            nearest_x = x1 + t * dx
            nearest_y = y1 + t * dy
            return sqrt((px - nearest_x) ** 2 + (py - nearest_y) ** 2)

        for line_obj in self.lines:
            x1, y1 = line_obj.start_pos
            x2, y2 = line_obj.end_pos
            distance = point_line_distance(x, y, x1, y1, x2, y2)
            if distance < threshold_distance:
                lines_to_remove.append(line_obj)
                self.canvas.remove(line_obj.line)

        for line in lines_to_remove:
            self.lines.remove(line)

        for ellipse_obj in self.ellipses:
            ex, ey = ellipse_obj.pos
            distance_to_ellipse = sqrt((x - ex) ** 2 + (y - ey) ** 2)
            if distance_to_ellipse < threshold_distance:
                ellipses_to_remove.append(ellipse_obj)
                self.canvas.remove(ellipse_obj.ellipse)

        for ellipse in ellipses_to_remove:
            self.ellipses.remove(ellipse)

        if self.lines:
            self.last_end_pos = self.lines[-1].end_pos
        else:
            self.last_end_pos = None

    def toggle_eraser(self):
        self.is_erasing = not self.is_erasing

    def undo(self):
        if self.undo_stack:
            last_line, last_ellipse = self.undo_stack.pop()
            if last_line in self.lines:
                self.lines.remove(last_line)
                self.canvas.remove(last_line.line)

            if last_ellipse in self.ellipses:
                self.ellipses.remove(last_ellipse)
                self.canvas.remove(last_ellipse.ellipse)

            if self.lines:
                self.last_end_pos = self.lines[-1].end_pos
            else:
                self.last_end_pos = None

class IconButton(ButtonBehavior, Image):
    pass

class DrawingApp(App):
    def build(self):
        main_layout = BoxLayout(orientation='horizontal')

        self.drawing_widget = DrawingWidget(size=(800, 600), size_hint=(0.8, 1))
        main_layout.add_widget(self.drawing_widget)

        controls_layout = BoxLayout(orientation='vertical', size_hint=(None, 1), width=120, spacing=10, padding=10)
        controls_layout.pos_hint = {'right': 1}

        with controls_layout.canvas.before:
            Color(1, 1, 1, 1)
            self.bg_rect = Rectangle(size=controls_layout.size, pos=controls_layout.pos)

        controls_layout.bind(size=self._update_bg_rect, pos=self._update_bg_rect)

        drawing_btn = IconButton(source='draw_icon.png', size_hint=(1, None), height=50)
        drawing_btn.bind(on_release=self.show_angle_popup)
        controls_layout.add_widget(drawing_btn)
        
        color_picker_btn = IconButton(source='color_icon.png', size_hint=(1, None), height=50)
        color_picker_btn.bind(on_release=self.show_color_picker)
        controls_layout.add_widget(color_picker_btn)
        
        eraser_btn = IconButton(source='eraser_icon.png', size_hint=(1, None), height=50)
        eraser_btn.bind(on_release=self.toggle_eraser)
        controls_layout.add_widget(eraser_btn)
        
        clear_btn = IconButton(source='clear_icon.png', size_hint=(1, None), height=50)
        clear_btn.bind(on_release=self.clear_canvas)
        controls_layout.add_widget(clear_btn)

        undo_btn = IconButton(source='undo_icon.png', size_hint=(1, None), height=50)
        undo_btn.bind(on_release=self.undo)
        controls_layout.add_widget(undo_btn)

        main_layout.add_widget(controls_layout)

        return main_layout

    def _update_bg_rect(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def show_angle_popup(self, instance):
        popup_layout = GridLayout(cols=1, padding=10, spacing=10)

        angles = [0, 45, 90]
        for angle in angles:
            angle_btn = Button(text=f'{angle}°', size_hint_y=None, height=40)
            angle_btn.bind(on_release=self.select_angle)
            popup_layout.add_widget(angle_btn)

        popup = Popup(title='Select Angle', content=popup_layout, size_hint=(0.3, 0.3))
        popup.open()

    def select_angle(self, instance):
        angle = int(instance.text.replace('°', ''))
        self.drawing_widget.set_angle(angle)

    def show_color_picker(self, instance):
        color_picker = ColorPicker()
        color_picker.bind(color=self.on_color)
        popup = Popup(title='Pick a Color', content=color_picker, size_hint=(0.5, 0.5))
        popup.open()

    def on_color(self, instance, value):
        self.drawing_widget.set_color(value)

    def toggle_eraser(self, instance):
        self.drawing_widget.toggle_eraser()

    def clear_canvas(self, instance):
        self.drawing_widget.clear_canvas()

    def undo(self, instance):
        self.drawing_widget.undo()

if __name__ == '__main__':
    DrawingApp().run()
