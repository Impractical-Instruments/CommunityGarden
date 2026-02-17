#include "OrbbecSensor/OrbbecSensorModule.h"

#include "Modules/ModuleManager.h"

#include "libobsensor/ObSensor.hpp"

DEFINE_LOG_CATEGORY(LogOrbbecSensor);

IMPLEMENT_MODULE(FOrbbecSensorModule, OrbbecSensor);

void FOrbbecSensorModule::StartupModule()
{
	// Set log level to reduce SDK noise in Unreal logs
	ob::Context::setLoggerSeverity(OB_LOG_SEVERITY_WARN);
}

void FOrbbecSensorModule::ShutdownModule() {}
