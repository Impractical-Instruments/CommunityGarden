#include "OrbbecSensor/OrbbecSensorModule.h"
#include "Modules/ModuleManager.h"

#if PLATFORM_WINDOWS
#include "Windows/AllowWindowsPlatformTypes.h"
#endif

#include "libobsensor/ObSensor.hpp"

#if PLATFORM_WINDOWS
#include "Windows/HideWindowsPlatformTypes.h"
#endif

IMPLEMENT_MODULE(FOrbbecSensorModule, OrbbecSensor);

void FOrbbecSensorModule::StartupModule()
{
	try
	{
		// Set log level to reduce SDK noise in Unreal logs
		ob::Context::setLoggerSeverity(OB_LOG_SEVERITY_WARN);
	}
	catch (ob::Error& e)
	{
		UE_LOG(LogTemp, Warning, TEXT("Failed to initialize Orbbec SDK Logger: %s"), *FString(e.getMessage()));
	}
}

void FOrbbecSensorModule::ShutdownModule() {}
