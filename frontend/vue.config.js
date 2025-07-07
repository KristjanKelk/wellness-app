const { defineConfig } = require('@vue/cli-service');
const webpack = require('webpack');
const path = require('path');

module.exports = defineConfig({
  // when you do `npm run build`, your dist/ will use "/" as the base
  publicPath: process.env.NODE_ENV === 'production' ? '/' : '/',
  outputDir:  'dist',
  assetsDir:  'static',

  transpileDependencies: true,

  configureWebpack: {
    plugins: [
      // this was your hydration flag
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