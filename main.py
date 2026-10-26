from vpython import *

scene = canvas(title='Управление нажатиями',
               width=2024, height=760,
               center=vector(0, 5, 0),
               background=color.white,
               autoscale=False)

floor = box(pos=vector(0, -0.5, 0), size=vector(200, 0.2, 200), color=color.green)

ball = sphere(pos=vector(0, 5, 0), radius=0.5, color=color.red)

vel_arrow = arrow(pos=ball.pos, axis=vector(0, 0, 0), shaftwidth=0.15, color=color.orange)

offset = vector(0, 2, -5)

scene.camera.pos = ball.pos + offset

scene.camera.axis = ball.pos - scene.camera.pos

ball.velocity = vector(0, 0, 0)
scene.camera.follow(ball)
g = vector(0, -9.8, 0)
impulsv = vector(0, 0, 0)
dt = 0.005
impulse = 1.0
drag_coeff = 0.5
max_thrust = 15.0   # максимальная мощность по каждой оси
lbl_thrust  = label(text='thrust: (0, 0, 0)',    pos=vector(80, 80, 0), height=14,
                    color=color.black, box=False, pixel_pos=True)
lbl_gravity = label(text='gravity: (0, -9.8, 0)', pos=vector(80, 60, 0), height=14,
                    color=color.black, box=False, pixel_pos=True)
lbl_total   = label(text='total force: (0, 0, 0)', pos=vector(80, 40, 0), height=14,
                    color=color.black, box=False, pixel_pos=True)
lbl_speed   = label(text='speed: 0',             pos=vector(80, 20, 0), height=14,
                    color=color.black, box=False, pixel_pos=True)

def on_key(evt):
    global impulsv
    k = evt.key
    if k == 'w': impulsv.z = min(impulsv.z + impulse,  max_thrust)
    if k == 's': impulsv.z = max(impulsv.z - impulse, -max_thrust)
    if k == 'd': impulsv.x = min(impulsv.x - impulse,  max_thrust)
    if k == 'a': impulsv.x = max(impulsv.x + impulse, -max_thrust)
    if k == 'e': impulsv.y = min(impulsv.y + impulse,  max_thrust)
    if k == 'q': impulsv.y = max(impulsv.y - impulse, -max_thrust)
    if k == 'r': impulsv = vector(0, 0, 0)
scene.bind('keydown', on_key)
# 4. Цикл анимации
while True:
    rate(200)
    # Наложение ускорения от клавиатуры + гравитации
    drag = -drag_coeff * ball.velocity  # сила против скорости
    ball.velocity += (g + impulsv + drag) * dt
    # Обновление положения
    ball.pos += ball.velocity * dt

    # Столкновение с землёй (отскок)
    if ball.pos.y < ball.radius:
        ball.pos.y = ball.radius
        ball.velocity.y = -ball.velocity.y * 0.8

    # Обновление вектора скорости
    vel_arrow.pos = ball.pos
    vel_arrow.axis = ball.velocity * 0.3
    lbl_thrust.text = f'thrust: ({impulsv.x:.1f}, {impulsv.y:.1f}, {impulsv.z:.1f})'
    lbl_gravity.text = f'gravity: ({g.x:.1f}, {g.y:.1f}, {g.z:.1f})'
    total = g + impulsv + drag
    lbl_total.text = f'total force: ({total.x:.1f}, {total.y:.1f}, {total.z:.1f})'
    lbl_speed.text = f'speed: {ball.velocity.mag:.2f}'