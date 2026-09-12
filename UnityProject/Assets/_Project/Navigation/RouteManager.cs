using UnityEngine;

namespace JiangchengUniversity.Navigation
{
    public sealed class RouteManager : MonoBehaviour
    {
        private void Awake()
        {
            DontDestroyOnLoad(gameObject);
            Debug.Log("[Stage A] RouteManager initialized.");
        }
    }
}
