<script>
export default {
  // ToDo replace with actual data calls
  data() {
    return {}
  }
}
</script>

<template>
  <div class="alert alert-info container fixed-top" ng-model="info" role="alert"
       style="display: none; z-index: 1080;"></div>
  <div class="alert alert-success container fixed-top" ng-model="success"
       style="display: none; z-index: 1090;"></div>
  <div class="alert alert-danger container fixed-top" ng-model="error"
       style="display: none; z-index: 1100;"></div>
</template>
