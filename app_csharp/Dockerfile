FROM mcr.microsoft.com/dotnet/sdk:9.0 AS build

WORKDIR /src

COPY modules_src/ .

RUN dotnet restore "index/index.csproj" \
    && dotnet publish "index/index.csproj" \
        -c Release \
        -o /publish/index \
        --no-restore \
        --self-contained false

RUN dotnet restore "health/health.csproj" \
    && dotnet publish "health/health.csproj" \
        -c Release \
        -o /publish/health \
        --no-restore \
        --self-contained false

RUN apt-get update && \
    apt-get install -y curl unzip && \
    rm -rf /var/lib/apt/lists/*

RUN curl -L -o ModuWeb.zip https://github.com/Chaleshka/ModuWeb/releases/download/v1.1.0/ModuWeb-linux-x64-v.1.1.0.zip \
    && mkdir mw \
    && mv ModuWeb.zip mw/ModuWeb.zip \
    && cd mw \
    && unzip ModuWeb.zip \
    && rm ModuWeb.zip \
    && chmod +x ModuWeb \
    && rm appsettings.json



FROM mcr.microsoft.com/dotnet/aspnet:9.0 AS final

WORKDIR /app

COPY --from=build /src/mw /app

COPY --from=build /src/health/bin/Release/net9.0/health.dll /app/modules/health.dll
COPY --from=build /src/index/bin/Release/net9.0/index.dll /app/modules/index.dll

RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser /app

COPY appsettings.json .

USER appuser

EXPOSE 5001

CMD ["./ModuWeb"]