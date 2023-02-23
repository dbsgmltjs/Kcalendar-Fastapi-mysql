FROM node:18.13.0-bullseye
WORKDIR /var/www/client/
COPY ./test_app/package.json .
RUN rm -rf node_modules && npm install -g npm@9.4.2
EXPOSE 19000
