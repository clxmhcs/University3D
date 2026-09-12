using UnityEngine;

namespace JiangchengUniversity.Performance
{
    public sealed class PerformanceManager : MonoBehaviour
    {
        private void Awake()
        {
            DontDestroyOnLoad(gameObject);
            Debug.Log("[Stage A] PerformanceManager initialized.");
        }
    }
}
