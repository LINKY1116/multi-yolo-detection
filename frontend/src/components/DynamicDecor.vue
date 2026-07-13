<template>
  <div class="dynamic-decor" aria-hidden="true">
    <span v-for="item in bubbles" :key="item" :class="`bubble bubble-${item}`"></span>
    <div class="grid-light"></div>
  </div>
</template>

<script>
export default {
  name: 'DynamicDecor',
  data() {
    return {
      bubbles: [1, 2, 3, 4, 5, 6]
    }
  }
}
</script>

<style scoped>
.dynamic-decor {
  position: fixed;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
  z-index: 0;
}

.grid-light {
  position: absolute;
  inset: 0;
  opacity: .28;
  background-image:
    linear-gradient(rgba(148, 163, 184, .13) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, .13) 1px, transparent 1px);
  background-size: 58px 58px;
  mask-image: linear-gradient(to bottom, transparent, #000 18%, #000 82%, transparent);
}

.bubble {
  position: absolute;
  display: block;
  border-radius: 999px;
  filter: blur(.2px);
  opacity: .65;
  animation: floatSoft 12s ease-in-out infinite;
}

.bubble-1 { width: 170px; height: 170px; left: 5%; top: 12%; background: rgba(199, 210, 254, .42); animation-delay: 0s; }
.bubble-2 { width: 105px; height: 105px; right: 10%; top: 16%; background: rgba(186, 230, 253, .48); animation-delay: -2s; }
.bubble-3 { width: 135px; height: 135px; left: 18%; bottom: 12%; background: rgba(254, 215, 170, .40); animation-delay: -4s; }
.bubble-4 { width: 90px; height: 90px; right: 22%; bottom: 18%; background: rgba(187, 247, 208, .38); animation-delay: -6s; }
.bubble-5 { width: 62px; height: 62px; right: 5%; bottom: 42%; background: rgba(221, 214, 254, .50); animation-delay: -8s; }
.bubble-6 { width: 76px; height: 76px; left: 46%; top: 8%; background: rgba(254, 202, 202, .32); animation-delay: -10s; }

@keyframes floatSoft {
  0%, 100% { transform: translate3d(0, 0, 0) scale(1); }
  50% { transform: translate3d(18px, -22px, 0) scale(1.06); }
}
</style>
