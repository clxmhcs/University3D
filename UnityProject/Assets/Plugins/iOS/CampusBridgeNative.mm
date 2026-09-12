#import <Foundation/Foundation.h>

typedef void (*CampusBridgeCallback)(const char *json);
static CampusBridgeCallback gCampusBridgeCallback = nullptr;

extern "C" void CampusBridge_RegisterCallback(CampusBridgeCallback callback)
{
    gCampusBridgeCallback = callback;
}

extern "C" void CampusBridge_SendToSwift(const char *json)
{
    if (json == nullptr)
    {
        return;
    }

    if (gCampusBridgeCallback != nullptr)
    {
        gCampusBridgeCallback(json);
        return;
    }

    NSLog(@"[CampusBridge] Swift callback has not been registered yet: %s", json);
}
