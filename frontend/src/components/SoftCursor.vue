<template>
  <div v-if="enabled" class="cursor-layer" aria-hidden="true">
    <div class="cursor-dot" :style="dotStyle"></div>
    <div class="cursor-ring" :style="ringStyle"></div>
  </div>
</template>

<script>
export default {
  name: 'SoftCursor',
  data() {
    return {
      enabled: false,
      x: 0,
      y: 0,
      ringX: 0,
      ringY: 0,
      rafId: null
    }
  },
  computed: {
    dotStyle() {
      return { transform: `translate3d(${this.x}px, ${this.y}px, 0)` }
    },
    ringStyle() {
      return { transform: `translate3d(${this.ringX}px, ${this.ringY}px, 0)` }
    }
  },
  mounted() {
    this.enabled = window.matchMedia('(pointer: fine)').matches && window.innerWidth > 768
    if (!this.enabled) return
    window.addEventListener('mousemove', this.handleMove, { passive: true })
    this.animate()
  },
  beforeUnmount() {
    window.removeEventListener('mousemove', this.handleMove)
    if (this.rafId) cancelAnimationFrame(this.rafId)
  },
  methods: {
    handleMove(event) {
      this.x = event.clientX
      this.y = event.clientY
    },
    animate() {
      this.ringX += (this.x - this.ringX) * 0.14
      this.ringY += (this.y - this.ringY) * 0.14
      this.rafId = requestAnimationFrame(this.animate)
    }
  }
}
</script>

<style scoped>
.cursor-layer {
  position: fixed;
  inset: 0;
  z-index: 9999;
  pointer-events: none;
}

.cursor-dot,
.cursor-ring {
  position: fixed;
  left: 0;
  top: 0;
  border-radius: 999px;
  pointer-events: none;
  will-change: transform;
}

.cursor-dot {
  width: 9px;
  height: 9px;
  margin: -4.5px 0 0 -4.5px;
  background: linear-gradient(135deg, #8ec5ff, #c9a7ff);
  box-shadow: 0 0 16px rgba(142, 197, 255, .75);
}

.cursor-ring {
  width: 38px;
  height: 38px;
  margin: -19px 0 0 -19px;
  border: 1px solid rgba(137, 160, 255, .45);
  background: rgba(255, 255, 255, .08);
  backdrop-filter: blur(2px);
}
</style>
