import { useState, useCallback, useEffect, useRef } from 'react';

/**
 * Hook for managing glass effect visibility
 */
export const useGlassEffect = (initialState: boolean = true) => {
  const [isVisible, setIsVisible] = useState(initialState);

  const toggleVisibility = useCallback(() => {
    setIsVisible((prev) => !prev);
  }, []);

  return {
    isVisible,
    toggleVisibility,
    glassClass: isVisible ? 'glass-neural' : 'glass-neural opacity-0',
  };
};

/**
 * Hook for managing animations
 */
export const useAnimation = (animationName: string, duration: number = 300) => {
  const [isAnimating, setIsAnimating] = useState(false);

  const trigger = useCallback(() => {
    setIsAnimating(true);
    const timer = setTimeout(() => setIsAnimating(false), duration);
    return () => clearTimeout(timer);
  }, [duration]);

  const animationClass = isAnimating ? animationName : '';

  return {
    isAnimating,
    trigger,
    animationClass,
  };
};

/**
 * Hook for managing loading states with neural shimmer
 */
export const useLoading = () => {
  const [isLoading, setIsLoading] = useState(false);

  const startLoading = useCallback(() => setIsLoading(true), []);
  const stopLoading = useCallback(() => setIsLoading(false), []);

  return {
    isLoading,
    startLoading,
    stopLoading,
    skeletonClass: isLoading ? 'skeleton loading-neural' : 'skeleton opacity-0',
  };
};

/**
 * Hook for managing confidence levels
 */
export const useConfidence = (level: number = 0) => {
  const getConfidenceClass = (confidence: number): string => {
    if (confidence >= 0.8) return 'confidence-high';
    if (confidence >= 0.5) return 'confidence-medium';
    return 'confidence-low';
  };

  const getConfidenceLabel = (confidence: number): string => {
    if (confidence >= 0.8) return 'High Confidence';
    if (confidence >= 0.5) return 'Medium Confidence';
    return 'Low Confidence';
  };

  const percentageLabel = Math.round(level * 100);

  return {
    confidenceClass: getConfidenceClass(level),
    label: getConfidenceLabel(level),
    percentage: percentageLabel,
  };
};

/**
 * Hook for managing chat message animations
 */
export const useChatMessage = (message: string) => {
  const [animateClass, setAnimateClass] = useState('');

  const animate = useCallback(() => {
    setAnimateClass('slide-in-up');
    const timer = setTimeout(() => setAnimateClass(''), 400);
    return () => clearTimeout(timer);
  }, []);

  return {
    message,
    animateClass,
    animate,
  };
};

/**
 * Hook for managing typing indicator
 */
export const useTypingIndicator = (isTyping: boolean = false) => {
  const [typing, setTyping] = useState(isTyping);

  return {
    isTyping: typing,
    setTyping,
    showTyping: typing,
  };
};

/**
 * Hook for managing hover effects
 */
export const useHoverClass = (hoverClass: string = 'hover-lift') => {
  const [isHovered, setIsHovered] = useState(false);

  const handlers = {
    onMouseEnter: () => setIsHovered(true),
    onMouseLeave: () => setIsHovered(false),
  };

  return {
    isHovered,
    handlers,
    className: isHovered ? hoverClass : '',
  };
};

/**
 * Hook for managing focus visible states
 */
export const useFocusVisible = () => {
  const [isFocused, setIsFocused] = useState(false);

  const handlers = {
    onFocus: () => setIsFocused(true),
    onBlur: () => setIsFocused(false),
  };

  return {
    isFocused,
    handlers,
    className: isFocused ? 'focus-ring' : '',
  };
};

/**
 * Hook for managing pulse animations
 */
export const usePulse = (shouldPulse: boolean = true) => {
  return {
    shouldPulse,
    pulseClass: shouldPulse ? 'neural-pulse' : '',
  };
};

/**
 * Hook for managing responsive breakpoints
 */
export const useResponsive = () => {
  const [windowSize, setWindowSize] = useState({
    width: typeof window !== 'undefined' ? window.innerWidth : 0,
  });

  useEffect(() => {
    const handleResize = () => {
      setWindowSize({ width: window.innerWidth });
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return {
    isMobile: windowSize.width < 768,
    isTablet: windowSize.width >= 768 && windowSize.width < 1024,
    isDesktop: windowSize.width >= 1024,
    width: windowSize.width,
  };
};

/**
 * Hook for creating neural ripple effect on click
 */
interface Ripple {
  id: number;
  x: number;
  y: number;
  size: number;
}

export const useNeuralRipple = () => {
  const [ripples, setRipples] = useState<Ripple[]>([]);

  const addRipple = useCallback((e: React.MouseEvent<HTMLElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = e.clientX - rect.left - size / 2;
    const y = e.clientY - rect.top - size / 2;

    const ripple: Ripple = {
      id: Date.now(),
      x,
      y,
      size,
    };

    setRipples((prev) => [...prev, ripple]);

    setTimeout(() => {
      setRipples((prev) => prev.filter((r) => r.id !== ripple.id));
    }, 600);
  }, []);

  return {
    ripples,
    addRipple,
  };
};

/**
 * Hook for managing threshold visibility (intersection observer)
 */
export const useThresholdVisibility = (ref: React.RefObject<HTMLElement>, threshold: number = 0.1) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsVisible(entry.isIntersecting);
      },
      { threshold }
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => {
      if (ref.current) {
        observer.unobserve(ref.current);
      }
    };
  }, [ref, threshold]);

  return isVisible;
};

/**
 * Hook for managing color schemes and themes
 */
export const useColorScheme = () => {
  const isDarkMode =
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-color-scheme: dark)').matches;

  return {
    isDarkMode,
    colors: {
      primary: '#6366F1',
      secondary: '#06B6D4',
      success: '#10B981',
      danger: '#EF4444',
      warning: '#F59E0B',
    },
  };
};

/**
 * Hook for managing debounced input
 */
export const useDebouncedInput = (initialValue: string = '', delay: number = 300) => {
  const [value, setValue] = useState(initialValue);
  const [debouncedValue, setDebouncedValue] = useState(initialValue);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => clearTimeout(timer);
  }, [value, delay]);

  return {
    value,
    setValue,
    debouncedValue,
  };
};

/**
 * Hook for managing async data loading with neural feedback
 */
export const useNeuralData = () => {
  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<any>(null);

  const fetchData = useCallback(async (promise: Promise<any>) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await promise;
      setData(result);
      return result;
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    data,
    isLoading,
    error,
    fetchData,
    loadingClass: isLoading ? 'processing' : '',
  };
};

/**
 * Hook for managing blur background on overlay
 */
export const useBlurBackground = (isOpen: boolean) => {
  useEffect(() => {
    if (isOpen) {
      document.body.style.filter = 'blur(2px)';
    } else {
      document.body.style.filter = 'none';
    }

    return () => {
      document.body.style.filter = 'none';
    };
  }, [isOpen]);

  return isOpen;
};
