const { defineConfig } = require('@vue/cli-service')
const webpack = require('webpack');
const path = require('path');

module.exports = defineConfig({
  transpileDependencies: true,
  configureWebpack: {
    plugins: [
      new webpack.DefinePlugin({
        __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: JSON.stringify(false)
      })
    ],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src/')
      }
    }
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