<template>
  <div id="app">
    <router-view />
    <SoftCursor />
  </div>
</template>

<script>
import SoftCursor from './components/SoftCursor.vue'

export default {
  name: 'App',
  components: {
    SoftCursor
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  min-height: 100vh;
}

body {
  margin: 0;
  overflow-x: hidden;
}

#app {
  min-height: 100vh;
}

a {
  color: inherit;
  text-decoration: none;
}
</style>
