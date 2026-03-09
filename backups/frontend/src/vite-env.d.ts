/// <reference types="vite/client" />

interface Window {
    Telegram: {
        WebApp: {
            ready: () => void;
            expand: () => void;
            close: () => void;
            initData: string;
            initDataUnsafe: any;
            MainButton: {
                text: string;
                show: () => void;
                hide: () => void;
                onClick: (cb: () => void) => void;
            };
            ThemeParams: any;
        };
    };
}
