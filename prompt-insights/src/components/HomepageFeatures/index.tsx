import type {ReactNode} from 'react';
import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

type FeatureItem = {
  title: string;
  Svg: React.ComponentType<React.ComponentProps<'svg'>>;
  description: ReactNode;
};

const FeatureList: FeatureItem[] = [
  {
    title: '실전 프롬프트 분석',
    Svg: require('@site/static/img/undraw_docusaurus_mountain.svg').default,
    description: (
      <>
        Cluely, Cursor, Perplexity 같은 <strong>실제 서비스</strong>에서 사용되는 
        프롬프트를 분석하여 검증된 패턴과 전략을 공유합니다.
      </>
    ),
  },
  {
    title: 'LLM 에이전트 최적화',
    Svg: require('@site/static/img/undraw_docusaurus_tree.svg').default,
    description: (
      <>
        역할 정의, 컨텍스트 관리, 도구 활용 등 <strong>에이전트 개발의 핵심 요소</strong>들을 
        체계적으로 분석하고 베스트 프랙티스를 제시합니다.
      </>
    ),
  },
  {
    title: '바로 적용 가능한 인사이트',
    Svg: require('@site/static/img/undraw_docusaurus_react.svg').default,
    description: (
      <>
        이론이 아닌 <strong>실무에서 바로 활용</strong>할 수 있는 프롬프트 패턴과 
        구현 가이드를 제공합니다.
      </>
    ),
  },
];

function Feature({title, Svg, description}: FeatureItem) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <Svg className={styles.featureSvg} role="img" />
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
