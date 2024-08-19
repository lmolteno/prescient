FROM sapmachine:11-jdk-headless-ubuntu-24.04
RUN apt-get update && apt-get install -y libgtk2.0-0t64
EXPOSE 8080:8080
RUN mkdir /app
COPY ./build/libs/*-all.jar /app/prescient.jar
ENTRYPOINT ["java","-jar","/app/prescient.jar"]