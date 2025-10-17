# Use a multi-stage build
FROM maven:3.8-openjdk-17 AS build

# Context is java-sdk/
# Build SDK first (assumes psor-sdk-lib exists in context)
WORKDIR /sdk
COPY ./psor-sdk-lib/pom.xml .
COPY ./psor-sdk-lib/src ./src
RUN mvn clean install 

# Now build the unblock plugin
WORKDIR /plugin
COPY ./unblock-ip-address/pom.xml .
COPY ./unblock-ip-address/src ./src
RUN mvn clean package -DskipTests

# Final stage
FROM openjdk:17-slim
WORKDIR /app
COPY --from=build /plugin/target/unblock-ip-1.0.jar .
ENTRYPOINT ["java", "-jar", "unblock-ip-1.0.jar"]
