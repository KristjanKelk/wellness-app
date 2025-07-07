// frontend/vue.config.js
const { defineConfig } = require('@vue/cli-service')
const webpack = require('webpack')
const path = require('path')

module.exports = defineConfig({
  // base URL for your app when deployed
  publicPath: process.env.NODE_ENV === 'production' ? '/' : '/',

  // where to put built files (for Django’s collectstatic)
  outputDir: path.resolve(__dirname, '../static/frontend'),

  // where to write index.html (so your Django templates can pick it up)
  indexPath: path.resolve(__dirname, '../templates/index.html'),

  // sub-folder under outputDir/static for js/css/img
  assetsDir: 'static',

  transpileDependencies: true,
  configureWebpack: {
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src/')
      }
    },
    plugins: [
      new webpack.DefinePlugin({
        __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: JSON.stringify(false)
      })
    ]
  },
  devServer: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    },
    webSocketServer: {
      options: {
        host: '0.0.0.0'
      }
    },
    client: {
      webSocketURL: {
        hostname: 'localhost',
        port: 8080
      },
    }
  }
})