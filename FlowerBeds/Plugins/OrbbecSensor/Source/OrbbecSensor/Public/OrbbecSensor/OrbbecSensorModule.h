#pragma once

#include "Modules/ModuleInterface.h"

class FOrbbecSensorModule : public IModuleInterface
{
public:
    virtual void StartupModule() override;
    virtual void ShutdownModule() override;
};
