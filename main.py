from ursina import *
import numpy as np
import math

app = Ursina()

# --- Параметры мира ---
ground = Entity(model='plane', scale=1000, color=color.gray, y=0, texture='white_cube', texture_scale=(100, 100))
Sky(color=color.rgb(255, 140, 100), shader=None)

# --- Параметры физики ---
NUM_DRONES = 5
MASS = 1.0
GRAVITY = np.array([0., -9.81, 0.])
THRUST_POWER = 30.0
DAMPING = 0.8

# Леннард-Джонс (взаимодействие только между ведомыми)
LJ_EPSILON = 2.0    # Сделали еще мягче
LJ_SIGMA = 8.0      # Равновесное расстояние

# Притяжение к лидеру
K_ATTRACT = 8.0    # Увеличили в 3 раза! Теперь дрон обязан лететь за лидером
LEADER_OFFSET = 1.0 # Убрали мертвую зону (работает почти всегда)
# Притяжение к лидеру

# --- ПАРАМЕТРЫ БЕЗОПАСНОСТИ ---
SAFE_RADIUS = 5.0           # Радиус, внутри которого лидер "отталкивает" ведомых
SOFT_REPEL_STRENGTH = 50.0  # Сила мягкого отталкивания (не жесткая пружина
# --- Параметры патрулирования ---
CIRCLE_RADIUS = 30.0   # Радиус круга
CIRCLE_SPEED = 10.0    # Скорость полёта по кругу (м/с)
CIRCLE_HEIGHT = 20.0   # Высота, на которой летает рой

patrol_angle = 0.0     # Текущий угол на окружности

# !)
class Drone(Entity):
    def __init__(self, position, is_leader=False, **kwargs):
        super().__init__(model='sphere', color=color.orange if is_leader else color.azure, scale=0.8, **kwargs)
        self.pos_np = np.array(position, dtype=float)
        self.vel_np = np.zeros(3)
        self.is_leader = is_leader
        self.position = Vec3(*self.pos_np)

        # --- Вектор направления (привязан к дрону) ---
        self.velocity_line = Entity(
            model='cube',
            color=color.red if is_leader else color.green,
            scale=(0.1, 0.1, 1),
            unlit=True,
            parent=self  # <-- ВАЖНО: привязка к дрону
        )
        self.velocity_line.z = 0.5 # Сдвигаем, чтобы линия начиналась из центра шара

        # --- Хвост ---
        self.trail_points = []
        self.trail_entities = []
        self.max_trail_length = 30  # Увеличили длину хвоста
        self.trail_color = color.orange if is_leader else color.cyan

    def update_visuals(self):
        # 1. Обновляем позицию шара
        self.position = Vec3(*self.pos_np)

        # 2. Обновляем вектор направления
        speed = np.linalg.norm(self.vel_np)
        if speed > 0.1:
            self.velocity_line.enabled = True
            # Вращаем линию в сторону скорости (относительно родителя)
            self.velocity_line.look_at(self.position + Vec3(*self.vel_np))
            # Масштаб по Z = скорость
            self.velocity_line.scale = (0.1, 0.1, speed * 0.5)
            # Сдвигаем так, чтобы начало было в центре
            self.velocity_line.z = self.velocity_line.scale_z / 2
        else:
            self.velocity_line.enabled = False

        # 3. Обновляем хвост
        self.trail_points.append(self.pos_np.copy())
        if len(self.trail_points) > self.max_trail_length:
            self.trail_points.pop(0)

        # Создаем визуальные точки хвоста, если их не хватает
        while len(self.trail_entities) < len(self.trail_points):
            t = Entity(model='sphere', scale=0.15, unlit=True)
            self.trail_entities.append(t)

        # Обновляем позиции и прозрачность точек хвоста
        for i, (p, entity) in enumerate(zip(self.trail_points, self.trail_entities)):
            entity.position = Vec3(*p)
            # Эффект затухания: старые точки бледнее
            fade = i / len(self.trail_points)
            entity.color = color.rgba(
                self.trail_color.r * 255,
                self.trail_color.g * 255,
                self.trail_color.b * 255,
                int(255 * fade)
            )

    def compute_acceleration(self, pos, vel, leader, all_drones):
        # ... ТВОЙ КОД compute_acceleration БЕЗ ИЗМЕНЕНИЙ ...
        force = MASS * GRAVITY
        '''
                if self.is_leader:
                    # Управление лидером
                    thrust = np.zeros(3)
                    if held_keys['w']: thrust[2] += 1
                    if held_keys['s']: thrust[2] -= 1
                    if held_keys['a']: thrust[0] -= 1
                    if held_keys['d']: thrust[0] += 1
                    if held_keys['space']: thrust[1] += 1
                    if held_keys['left shift']: thrust[1] -= 1

                    if np.linalg.norm(thrust) > 0:
                        thrust = thrust / np.linalg.norm(thrust) * THRUST_POWER
                    force += thrust
        '''
        if self.is_leader:
            # Вычисляем текущую цель на окружности (угол обновляется в update())
            target_x = CIRCLE_RADIUS * math.cos(patrol_angle)
            target_z = CIRCLE_RADIUS * math.sin(patrol_angle)
            target_pos = np.array([target_x, CIRCLE_HEIGHT, target_z])

            # Вектор к цели
            to_target = target_pos - pos
            dist = np.linalg.norm(to_target)

            # Автопилот: летим к цели с силой, пропорциональной расстоянию
            if dist > 0.1:
                force += (to_target / dist) * 50.0 * MASS  # Сила автопилота

        else:
            # 1. Притяжение к лидеру
            to_leader = leader.pos_np - pos
            dist_to_leader = np.linalg.norm(to_leader)
            if dist_to_leader > 1e-3:
                stretch = min(dist_to_leader, 15.0)
                force += (to_leader / dist_to_leader) * K_ATTRACT * MASS * (stretch / 5.0)

            # 2. Упреждающее избегание
            look_ahead_time = 2
            future_leader_pos = leader.pos_np + leader.vel_np * look_ahead_time
            to_future_leader = future_leader_pos - pos
            dist_to_future = np.linalg.norm(to_future_leader)
            if dist_to_future < SAFE_RADIUS and dist_to_future > 1e-3:
                ratio = (SAFE_RADIUS - dist_to_future) / SAFE_RADIUS
                evade_dir = -to_future_leader / dist_to_future
                force += evade_dir * SOFT_REPEL_STRENGTH * (ratio ** 2) * MASS

            # 3. Леннард-Джонс
            for other in all_drones:
                if other is self: continue
                if other.is_leader: continue
                r_vec = pos - other.pos_np
                r = np.linalg.norm(r_vec)
                if r < 1e-6: continue
                if r < LJ_SIGMA * 0.5:
                    force += (r_vec / r) * 100.0 * MASS
                    continue
                sr6 = (LJ_SIGMA / r) ** 6
                sr12 = sr6 ** 2
                force_magnitude = 24.0 * LJ_EPSILON * (2.0 * sr12 - sr6) / (r * r)
                force_magnitude = np.clip(force_magnitude, -100, 100)
                force += force_magnitude * r_vec

        # 4. Демпфер
        force += -DAMPING * vel
        return force / MASS

    def step_rk4(self, dt, leader, all_drones):
        # ... ТВОЙ КОД RK4 ...
        v1 = self.vel_np
        a1 = self.compute_acceleration(self.pos_np, v1, leader, all_drones)

        v2 = self.vel_np + 0.5 * dt * a1
        p2 = self.pos_np + 0.5 * dt * v1
        a2 = self.compute_acceleration(p2, v2, leader, all_drones)

        v3 = self.vel_np + 0.5 * dt * a2
        p3 = self.pos_np + 0.5 * dt * v2
        a3 = self.compute_acceleration(p3, v3, leader, all_drones)

        v4 = self.vel_np + dt * a3
        p4 = self.pos_np + dt * v3
        a4 = self.compute_acceleration(p4, v4, leader, all_drones)

        self.vel_np += (dt / 6.0) * (a1 + 2 * a2 + 2 * a3 + a4)
        self.pos_np += (dt / 6.0) * (v1 + 2 * v2 + 2 * v3 + v4)

        if self.pos_np[1] < 0.5:
            self.pos_np[1] = 0.5
            if self.vel_np[1] < 0:
                self.vel_np[1] = 0

        # ВМЕСТО self.position = Vec3(*self.pos_np) вызываем:
        self.update_visuals()


class DebugUI(Entity):
    def __init__(self, leader, drones, **kwargs):
        super().__init__(parent=camera.ui, **kwargs)
        self.leader = leader
        self.drones = drones

        # Текст с параметрами
        self.text = Text(
            text="",
            position=(-0.85, 0.45),
            scale=1.0,
            color=color.white,
            background=True,
            background_color=color.rgba(0, 0, 0, 150)
        )

    def update(self):
        # 1. Параметры лидера
        l_speed = np.linalg.norm(self.leader.vel_np)
        l_pos = self.leader.pos_np

        # 2. Среднее расстояние до ведомых
        distances = []
        for d in self.drones:
            if not d.is_leader:
                distances.append(np.linalg.norm(d.pos_np - self.leader.pos_np))

        avg_dist = np.mean(distances) if distances else 0
        min_dist = np.min(distances) if distances else 0
        max_dist = np.max(distances) if distances else 0

        # 3. Средняя скорость роя
        speeds = [np.linalg.norm(d.vel_np) for d in self.drones if not d.is_leader]
        avg_speed = np.mean(speeds) if speeds else 0

        # Формируем текст на русском
        text = (
            f"=== ЛИДЕР ===\n"
            f"Скорость: {l_speed:.2f} м/с\n"
            f"Позиция: X:{l_pos[0]:.1f} Y:{l_pos[1]:.1f} Z:{l_pos[2]:.1f}\n"
            f"\n"
            f"=== РОЙ ===\n"
            f"Дистанция до лидера:\n"
            f"  Средняя: {avg_dist:.1f} м\n"
            f"  Мин: {min_dist:.1f} м\n"
            f"  Макс: {max_dist:.1f} м\n"
            f"Средняя скорость: {avg_speed:.2f} м/с\n"
            f"\n"
            f"=== ФИЗИКА (клавиши) ===\n"
            f"Сила притяжения [1/2]: {K_ATTRACT:.1f}\n"
            f"Сила Леннарда-Джонса [3/4]: {LJ_EPSILON:.1f}\n"
            f"Равновесное расстояние [5/6]: {LJ_SIGMA:.1f}\n"
            f"Скорость по кругу [7/8]: {CIRCLE_SPEED:.1f}\n"
            f"Демпфер [9/0]: {DAMPING:.1f}\n"
            f"\n"
            f"=== ОКРУЖНОСТЬ ===\n"
            f"Радиус круга [Q/W]: {CIRCLE_RADIUS:.1f}\n"
            f"Высота полета [E/R]: {CIRCLE_HEIGHT:.1f}\n"
        )
        self.text.text = text
# --- Инициализация дронов ---
drones = []
# Лидер в центре
drones.append(Drone((0, 8, 0), is_leader=True))
leader = drones[0]

# Спавним ведомых вокруг лидера по кругу
import math

SPAWN_RADIUS = 8.0  # Радиус круга, по которому они появляются (должен быть около LJ_SIGMA)
for i in range(1, NUM_DRONES):
    # Распределяем углы равномерно (360 градусов / количество ведомых)
    angle = (i - 1) * (2 * math.pi / (NUM_DRONES - 1))

    # Вычисляем координаты на круге (в горизонтальной плоскости XZ)
    spawn_x = leader.position.x + SPAWN_RADIUS * math.cos(angle)
    spawn_z = leader.position.z + SPAWN_RADIUS * math.sin(angle)
    spawn_y = leader.position.y  # На той же высоте, что и лидер

    drones.append(Drone((spawn_x, spawn_y, spawn_z), is_leader=False))

# --- Динамическое изменение параметров ---
# Мы будем менять глобальные переменные при нажатии клавиш
change_speed = 1.0  # Шаг изменения


def input(key):
    global K_ATTRACT, LJ_EPSILON, LJ_SIGMA, CIRCLE_SPEED, CIRCLE_RADIUS, CIRCLE_HEIGHT, DAMPING

    # Притяжение к лидеру
    if key == '1': K_ATTRACT += 1.0
    if key == '2': K_ATTRACT = max(0, K_ATTRACT - 1.0)

    # Сила Леннарда-Джонса
    if key == '3': LJ_EPSILON += 0.5
    if key == '4': LJ_EPSILON = max(0, LJ_EPSILON - 0.5)

    # Равновесное расстояние
    if key == '5': LJ_SIGMA += 0.5
    if key == '6': LJ_SIGMA = max(1.0, LJ_SIGMA - 0.5)

    # Скорость полёта по кругу
    if key == '7': CIRCLE_SPEED += 1.0
    if key == '8': CIRCLE_SPEED = max(0, CIRCLE_SPEED - 1.0)

    # Демпфер
    if key == '9': DAMPING += 0.1
    if key == '0': DAMPING = max(0.0, DAMPING - 0.1)

    # --- НОВОЕ: Окружность ---
    # Радиус (Q / W)
    if key == 'q': CIRCLE_RADIUS += 2.0
    if key == 'w': CIRCLE_RADIUS = max(5.0, CIRCLE_RADIUS - 2.0)

    # Высота (E / R)
    if key == 'e': CIRCLE_HEIGHT += 2.0
    if key == 'r': CIRCLE_HEIGHT = max(2.0, CIRCLE_HEIGHT - 2.0)
# --- Управление камерой через стрелки ---
# class ArrowCamera(Entity):
#     def __init__(self, target, **kwargs):
#         super().__init__(**kwargs)
#         self.target = target
#         self.distance = 28.0
#         self.yaw = 0.0
#         self.pitch = 150
#         self.speed = 60.0
#
#         self.update_camera()
#
#     def update_camera(self):
#         yaw_rad = math.radians(self.yaw)
#         pitch_rad = math.radians(self.pitch)
#
#         ox = self.distance * math.cos(pitch_rad) * math.sin(yaw_rad)
#         oy = self.distance * math.sin(pitch_rad)
#         oz = self.distance * math.cos(pitch_rad) * math.cos(yaw_rad)
#
#         camera.position = self.target.position + Vec3(ox, oy, oz)
#         camera.look_at(self.target.position)
#
#     def update(self):
#         if held_keys['left arrow']:
#             self.yaw -= self.speed * time.dt
#         if held_keys['right arrow']:
#             self.yaw += self.speed * time.dt
#         if held_keys['up arrow']:
#             self.pitch += self.speed * time.dt
#             self.pitch = min(self.pitch, 180)
#         if held_keys['down arrow']:
#             self.pitch -= self.speed * time.dt
#             self.pitch = max(self.pitch, 5)
#
#         self.update_camera()
#
#     def input(self, key):
#         if key == 'scroll up':
#             self.distance = max(5, self.distance - 2)
#             self.update_camera()
#         elif key == 'scroll down':
#             self.distance = min(100, self.distance + 2)
#             self.update_camera()


camera.position = (0, 30, -100)
camera.look_at(Vec3(0, 5, 0))


def update():
    global  patrol_angle
    dt = min(time.dt, 0.05)
    patrol_angle += (CIRCLE_SPEED / CIRCLE_RADIUS) * dt

    for d in drones:
        d.step_rk4(dt, leader, drones)

debug_ui = DebugUI(leader, drones)
app.run()