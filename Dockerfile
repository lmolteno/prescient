FROM sapmachine:22-jre-headless-ubuntu-22.04
RUN apt-get update && apt-get install -y libgtk2.0-0t64
EXPOSE 8080:8080
RUN mkdir /app
COPY ./build/libs/*-all.jar /app/prescient.jar
ENTRYPOINT ["java","-jar","/app/prescient.jar"]