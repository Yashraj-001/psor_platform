# Use a multi-stage build
FROM maven:3.8-openjdk-17 AS build

# Context is now java-sdk/
# Build SDK first
WORKDIR /sdk
COPY ./psor-sdk-lib/pom.xml .
COPY ./psor-sdk-lib/src ./src
RUN mvn clean install # Install SDK to local Maven repo

# Now build the plugin
WORKDIR /plugin
COPY ./block-ip-address/pom.xml .
COPY ./block-ip-address/src ./src
RUN mvn clean package -DskipTests

# Final stage
FROM openjdk:17-slim
WORKDIR /app
COPY --from=build /plugin/target/block-ip-1.0.jar .
ENTRYPOINT ["java", "-jar", "block-ip-1.0.jar"]
