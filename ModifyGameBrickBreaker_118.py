import tkinter as tk
import random

#membuat class untuk semua objek game
class GameObject(object):
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):#Mengembalikan posisi berdasarkan koordinat kanvas
        return self.canvas.coords(self.item)

    def move(self, x, y): # 
        self.canvas.move(self.item, x, y)

    def delete(self): #Menghapus objek dari canvas
        self.canvas.delete(self.item)

#mengatur gerakan bola, pembalikan arah saat bertabrakan dengan objek, dan deteksi tabrakan.
class Ball(GameObject):
    def __init__(self, canvas, x, y):
        self.radius = 10
        self.direction = [1, -1]
        self.speed = 6
        item = canvas.create_oval(x - self.radius, y - self.radius,
                                  x + self.radius, y + self.radius,
                                  fill='beige')
        super(Ball, self).__init__(canvas, item)

    def update(self):#Memperbarui posisi bola berdasarkan arah dan kecepatan
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] <= 0 or coords[2] >= width:
            self.direction[0] *= -1
        if coords[1] <= 0:
            self.direction[1] *= -1
        x = self.direction[0] * self.speed
        y = self.direction[1] * self.speed
        self.move(x, y)

    def collide(self, game_objects):#Memeriksa tabrakan bola dengan objek game lainnya dan membalikkan arah bola sesuai dengan objek yang terkena.
        coords = self.get_position()
        x = (coords[0] + coords[2]) * 0.5
        if len(game_objects) > 1:
            self.direction[1] *= -1
        elif len(game_objects) == 1:
            game_object = game_objects[0]
            coords = game_object.get_position()
            if x > coords[2]:
                self.direction[0] = 1
            elif x < coords[0]:
                self.direction[0] = -1
            else:
                self.direction[1] *= -1

        for game_object in game_objects:
            if isinstance(game_object, Brick):
                game_object.hit()

#mengatur paddle (papan penggerak) yang digunakan untuk memantulkan bola
class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        self.width = 80
        self.height = 10
        self.ball = None
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill='#E1C6A3')
        super(Paddle, self).__init__(canvas, item)

    def set_ball(self, ball):#Menetapkan bola yang akan di pantukkan
        self.ball = ball

    def move(self, offset):#Menggerakkan paddle dengan offset horizontal, dengan batasan agar paddle tidak keluar dari canvas
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] + offset >= 0 and coords[2] + offset <= width:
            super(Paddle, self).move(offset, 0)
            if self.ball is not None:
                self.ball.move(offset, 0)

    def expand(self): #Mengatur lebar dan panjang paddle
        self.width += 40
        coords = self.get_position()
        self.canvas.coords(self.item,
                           coords[0] - 20, coords[1],
                           coords[2] + 20, coords[3])

#mengatur brick brick yang ada di layar yang harus dihancurkan oleh bola.
class Brick(GameObject):
    COLORS = {1: '#F6E3B4', 2: '#F7C4A3', 3: '#F4C2C2'}

    def __init__(self, canvas, x, y, hits):
        self.width = 75
        self.height = 20
        self.hits = hits
        color = Brick.COLORS[hits]
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill=color, tags='brick')
        super(Brick, self).__init__(canvas, item)

    def hit(self):#Menurunkan jumlah hits dan mengubah warna brick berdasarkan jumlah hits yang tersisa
        self.hits -= 1
        if self.hits == 0:
            self.delete()
        else:
            self.canvas.itemconfig(self.item,
                                   fill=Brick.COLORS[self.hits])

#Mengelola keseluruhan game, termasuk game loop, skor, nyawa
class Game(tk.Frame):
    def __init__(self, master):
        super(Game, self).__init__(master)
        self.lives = 3
        self.score = 0
        self.level = 1
        self.paused = False
        self.width = 610
        self.height = 400
        self.canvas = tk.Canvas(self, bg='#F7C6C7',
                                width=self.width,
                                height=self.height)
        self.canvas.pack()
        self.pack()

        self.items = {}
        self.ball = None
        self.paddle = Paddle(self.canvas, self.width / 2, 326)
        self.items[self.paddle.item] = self.paddle

        self.hud = None
        self.score_display = None
        self.text = None
        self.setup_game()
        self.canvas.focus_set()
        self.canvas.bind('<Left>',
                         lambda _: self.paddle.move(-10))
        self.canvas.bind('<Right>',
                         lambda _: self.paddle.move(10))
        self.canvas.bind('p', lambda _: self.pause_game())
        self.canvas.bind('r', lambda _: self.resume_game())

    def setup_game(self):#Menyiapkan elemen-elemen game, termasuk menambahkan bola, memperbarui teks skor dan nyawa, serta menyiapkan brick.
        self.add_ball()
        self.update_lives_text()
        self.update_score_text()
        self.text = self.draw_text(300, 200,
                                   'Press Space to start')
        self.canvas.bind('<space>', lambda _: self.start_game())
        self.reset_bricks()

    def add_ball(self):#Membuat objek bola baru dan menghubungkannya ke paddle.
        if self.ball is not None:
            self.ball.delete()
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        self.ball = Ball(self.canvas, x, 310)
        self.paddle.set_ball(self.ball)

    def reset_bricks(self):#Menatur ulang kondisi da posisi brick
        for x in range(5, self.width - 5, 75):
            for y, hits in zip(range(50, 120, 20), [3, 2, 1]):
                self.add_brick(x + 37.5, y, hits)

    def add_brick(self, x, y, hits): #  Membuat brick bary di lokasi dan jumlah yang di tentukan
        brick = Brick(self.canvas, x, y, hits)
        self.items[brick.item] = brick

    def draw_text(self, x, y, text, size='40'):#menampilkan teks dilayar dengan ukurn font yang telah di tentukan
        font = ('lato', size)
        return self.canvas.create_text(x, y, text=text,
                                       font=font)

    def update_lives_text(self):#Memperbarui teks
        text = f'Lives: {self.lives}'
        if self.hud is None:
            self.hud = self.draw_text(50, 20, text, 15)
        else:
            self.canvas.itemconfig(self.hud, text=text)

    def update_score_text(self):#Memperbarui skor pemain
        text = f'Score: {self.score}'
        if self.score_display is None:
            self.score_display = self.draw_text(550, 20, text, 15)
        else:
            self.canvas.itemconfig(self.score_display, text=text)

    def start_game(self):#memulai permainan dengan menghapus teks "Press Space To Start" dan memulai permainan
        self.canvas.unbind('<space>')
        self.canvas.delete(self.text)
        self.text = None
        self.paddle.ball = None
        self.game_loop()

    def game_loop(self):
        if not self.paused:
            self.check_collisions()
            num_bricks = len(self.canvas.find_withtag('brick'))
            if num_bricks == 0:
                self.level += 1
                self.ball.speed += 1
                self.setup_game()
            elif self.ball.get_position()[3] >= self.height:
                self.ball.speed = None
                self.lives -= 1
                if self.lives < 0:
                    self.draw_text(300, 200, 'Game Over!')
                else:
                    self.after(1000, self.setup_game)
            else:
                self.ball.update()
                self.after(50, self.game_loop)

    def check_collisions(self):
        ball_coords = self.ball.get_position()
        items = self.canvas.find_overlapping(*ball_coords)
        objects = [self.items[x] for x in items if x in self.items]
        self.ball.collide(objects)
        for obj in objects:
            if isinstance(obj, Brick):
                self.score += 10
                self.update_score_text()

    def pause_game(self):#Menjeda permainan dan menampilkan pesan "Game Paused" di layar.
        self.paused = True
        self.canvas.delete(self.text)  # Make sure to delete any existing text
        self.text = self.draw_text(300, 200, 'Game Paused. Press R to Resume')

    def resume_game(self):#Melanjutkan permainan setelah dijeda
        if self.paused:
            self.paused = False
            self.canvas.delete(self.text)
            self.text = None
            self.canvas.bind('<space>', lambda _: self.start_game())
            self.game_loop()


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Break the Bricks!')
    game = Game(root)
    game.mainloop()

#syarat untuk mempause dengan menggunakn tombol'p' dan resume dengan tombol 'r'