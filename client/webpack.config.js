const path = require('path');

module.exports = {
  devServer: {
    contentBase: path.join(__dirname, 'public')
  },
  devtool: 'cheap-module-eval-source-map',
  entry: './src/index.jsx',
  module: {
    rules: [
      {
        test: /\.jsx?$/,
        exclude: /node_modules/,
        loader: 'babel-loader'
      }
    ]
  },
  output: {
    filename: 'client.js',
    path: path.resolve(__dirname, 'dist'),
  },
};
