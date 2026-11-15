from manim import *

class TimelinePoc(Scene):
    def construct(self):
        title = Text("日本のあゆみ", font="Hiragino Sans", font_size=54, color=WHITE).to_edge(UP, buff=0.7)
        self.play(FadeIn(title, shift=DOWN * 0.3), run_time=0.7)
        line = Line(LEFT * 6.2, RIGHT * 6.2, color=YELLOW, stroke_width=8).shift(DOWN * 0.2)
        self.play(Create(line), run_time=1.2)
        eras = [("旧石器", "約3万年前"), ("縄文", "約1万年前"), ("弥生", "約2300年前"), ("古墳", "約1750年前")]
        xs = [-4.65, -1.55, 1.55, 4.65]
        for (name, sub), x in zip(eras, xs):
            dot = Dot(point=[x, -0.2, 0], color=YELLOW, radius=0.11)
            label = Text(name, font="Hiragino Sans", font_size=44, color=WHITE).next_to(dot, UP, buff=0.35)
            sub_t = Text(sub, font="Hiragino Sans", font_size=30, color="#BBBBBB").next_to(dot, DOWN, buff=0.35)
            self.play(FadeIn(dot, scale=0.3), FadeIn(label, shift=UP * 0.2), FadeIn(sub_t), run_time=0.55)
        self.wait(0.8)
