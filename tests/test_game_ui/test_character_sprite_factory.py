import pygame

from game_ui.world_rendering.character_sprite_factory import (
    ProceduralCharacterSpriteFactory,
)


def test_factory_builds_eight_direction_idle_walk_and_run_animations():
    animator = ProceduralCharacterSpriteFactory().create_animator(pygame)

    assert len(animator.animations) == 8 * 3
    for direction in ProceduralCharacterSpriteFactory.DIRECTIONS:
        for state in ("idle", "walk", "run"):
            animator.select(direction=direction, state=state)
            frame = animator.current_frame
            assert frame.get_size() == (48, 64)
            assert frame.get_bounding_rect().width > 0


def test_walk_and_run_use_eight_distinct_animation_frames():
    animator = ProceduralCharacterSpriteFactory().create_animator(pygame)

    for direction in ProceduralCharacterSpriteFactory.DIRECTIONS:
        for state in ("walk", "run"):
            animation = animator.animations[(direction, state)]
            assert len(animation.frames) == 8
            expected_duration = 0.075 if state == "walk" else 0.055
            assert animation.frame_duration == expected_duration

            lower_body_frames = {
                pygame.image.tostring(frame.subsurface((0, 43, 48, 21)), "RGBA")
                for frame in animation.frames
            }
            assert len(lower_body_frames) == 8


def test_direction_change_preserves_locomotion_phase():
    animator = ProceduralCharacterSpriteFactory().create_animator(pygame)
    animator.select(direction="south", state="walk")
    animator.update(0.08)
    previous_animation = animator.current_animation
    assert previous_animation.index == 1

    animator.select(direction="east", state="walk")
    assert animator.current_animation.index == previous_animation.index
    assert abs(
        animator.current_animation.elapsed - previous_animation.elapsed
    ) < 1e-9


def test_animation_state_change_restarts_the_selected_clip():
    animator = ProceduralCharacterSpriteFactory().create_animator(pygame)
    animator.select(direction="south", state="walk")
    animator.update(0.08)

    animator.select(state="run")
    assert animator.current_animation.index == 0
    assert animator.current_animation.elapsed == 0.0
